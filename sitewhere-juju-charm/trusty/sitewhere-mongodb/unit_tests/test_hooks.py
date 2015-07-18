from mock import patch, call

import hooks

from test_utils import CharmTestCase
from pymongo.errors import OperationFailure
from subprocess import CalledProcessError

# Defines a set of functions to patch on the hooks object. Any of these
# methods will be patched by default on the default invocations of the
# hooks.some_func(). Invoking the the interface change relations will cause
# the hooks context to be created outside of the normal mockery.
TO_PATCH = [
    'relation_id',
    'relation_get',
    'relation_set',
    'unit_get',
    'juju_log',
    'config',
]


class MongoHooksTest(CharmTestCase):

    def setUp(self):
        super(MongoHooksTest, self).setUp(hooks, TO_PATCH)

        # The self.config object can be used for direct invocations of the
        # hooks methods. The side_effect of invoking the config object within
        # the hooks object will return the value that is set in the test case's
        # test_config dictionary
        self.config.side_effect = self.test_config.get
        self.relation_get.side_effect = self.test_relation.get

    @patch.object(hooks, 'restart_mongod')
    @patch.object(hooks, 'enable_replset')
    # Note: patching the os.environ dictionary in-line here so there's no
    # additional parameter sent into the function
    @patch.dict('os.environ', JUJU_UNIT_NAME='fake-unit/0')
    def test_replica_set_relation_joined(self, mock_enable_replset,
                                         mock_restart):
        self.unit_get.return_value = 'private.address'
        self.test_config.set('port', '1234')
        self.test_config.set('replicaset', 'fake-replicaset')
        self.relation_id.return_value = 'fake-relation-id'

        mock_enable_replset.return_value = False

        hooks.replica_set_relation_joined()

        # Verify that mongodb was NOT restarted since the replicaset we claimed
        # was not enabled.
        self.assertFalse(mock_restart.called)

        exp_rel_vals = {'hostname': 'private.address',
                        'port': '1234',
                        'replset': 'fake-replicaset',
                        'install-order': '0',
                        'type': 'replset'}
        # Check that the relation data was set as we expect it to be set.
        self.relation_set.assert_called_with('fake-relation-id', exp_rel_vals)

        mock_enable_replset.reset_mock()
        self.relation_set.reset_mock()
        mock_enable_replset.return_value = True

        hooks.replica_set_relation_joined()

        self.assertTrue(mock_restart.called)
        self.relation_set.assert_called_with('fake-relation-id', exp_rel_vals)

    @patch.object(hooks, 'run_admin_command')
    @patch.object(hooks, 'Connection')
    @patch.object(hooks, 'config')
    @patch.object(hooks, 'mongo_client')
    @patch('time.sleep')
    def test_init_repl_set(self, mock_sleep, mock_mongo_client_fn,
                           mock_config, mock_mongo_client,
                           mock_run_admin_command):
        mock_mongo_client_fn.return_value = False

        mock_config.return_value = {'replicaset': 'foo',
                                    'private-address': 'mongo.local',
                                    'port': '12345'}

        # Put the OK state (1) at the end and check the loop.
        ret_values = [{'myState': x} for x in [0, 2, 5, 1]]
        mock_run_admin_command.side_effect = ret_values

        hooks.init_replset()

        mock_run_admin_command.assert_called()
        self.assertEqual(len(ret_values), mock_run_admin_command.call_count)
        self.assertEqual(len(ret_values) + 1, mock_sleep.call_count)

        mock_run_admin_command.reset_mock()
        exc = [OperationFailure('Received replSetInitiate'),
               OperationFailure('unhandled')]
        mock_run_admin_command.side_effect = exc

        try:
            hooks.init_replset()
            self.assertTrue(False, msg="Expected error")
        except OperationFailure:
            pass

        mock_run_admin_command.assert_called()
        self.assertEqual(2, mock_run_admin_command.call_count)

    @patch.object(hooks, 'mongo_client_smart')
    def test_join_replset(self, mock_mongo_client):
        hooks.join_replset()
        self.assertFalse(mock_mongo_client.called)

        mock_mongo_client.reset_mock()
        hooks.join_replset(master_node='mongo.local')
        self.assertFalse(mock_mongo_client.called)

        mock_mongo_client.reset_mock()
        hooks.join_replset(host='fake-host')
        self.assertFalse(mock_mongo_client.called)

        mock_mongo_client.reset_mock()
        hooks.join_replset(master_node='mongo.local', host='fake-host')
        mock_mongo_client.assert_called_with('localhost',
                                             'rs.add("fake-host")')

    @patch.object(hooks, 'mongo_client')
    def test_leave_replset(self, mock_mongo_client):
        hooks.leave_replset()
        self.assertFalse(mock_mongo_client.called)

        mock_mongo_client.reset_mock()
        hooks.leave_replset(master_node='mongo.local')
        self.assertFalse(mock_mongo_client.called)

        mock_mongo_client.reset_mock()
        hooks.leave_replset(host='fake-host')
        self.assertFalse(mock_mongo_client.called)

        mock_mongo_client.reset_mock()
        hooks.leave_replset('mongo.local', 'fake-host')
        mock_mongo_client.assert_called_with('mongo.local',
                                             'rs.remove("fake-host")')

    @patch.object(hooks, 'apt_install')
    @patch.object(hooks, 'apt_update')
    @patch.object(hooks, 'add_source')
    @patch.dict('os.environ', CHARM_DIR='/tmp/charm/dir')
    def test_install_hook(self, mock_add_source, mock_apt_update,
                          mock_apt_install):
        self.test_config.set('source', 'fake-source')
        self.test_config.set('key', 'fake-key')

        hooks.install_hook()
        mock_add_source.assert_called_with('fake-source', 'fake-key')
        mock_apt_update.assert_called_with(fatal=True)
        mock_apt_install.assert_called_with(packages=hooks.INSTALL_PACKAGES,
                                            fatal=True)

    @patch.object(hooks, 'run_admin_command')
    @patch.object(hooks, 'Connection')
    @patch('time.sleep')
    def test_am_i_primary(self, mock_sleep, mock_mongo_client,
                          mock_run_admin_cmd):
        mock_run_admin_cmd.side_effect = [{'myState': x} for x in xrange(5)]
        expected_results = [True if x == 1 else False for x in xrange(5)]

        # Check expected return values each time...
        for exp in expected_results:
            rv = hooks.am_i_primary()
            self.assertEqual(exp, rv)

    @patch.object(hooks, 'run_admin_command')
    @patch.object(hooks, 'Connection')
    @patch('time.sleep')
    def test_am_i_primary_too_many_attempts(self, mock_sleep,
                                            mock_mongo_client,
                                            mock_run_admin_cmd):
        msg = 'replSetInitiate - should come online shortly'
        mock_run_admin_cmd.side_effect = [OperationFailure(msg)
                                          for x in xrange(10)]

        try:
            hooks.am_i_primary()
            self.assertTrue(False, 'Expected failure.')
        except hooks.TimeoutException:
            self.assertEqual(mock_run_admin_cmd.call_count, 10)
            pass

    @patch.object(hooks, 'run_admin_command')
    @patch.object(hooks, 'Connection')
    @patch('time.sleep')
    def test_am_i_primary_operation_failures(self, mock_sleep,
                                             mock_mongo_client,
                                             mock_run_admin_cmd):
        mock_run_admin_cmd.side_effect = OperationFailure('EMPTYCONFIG')

        rv = hooks.am_i_primary()
        mock_run_admin_cmd.assert_called()
        self.assertFalse(rv)

        mock_run_admin_cmd.reset_mock()
        mock_run_admin_cmd.side_effect = OperationFailure('unexpected failure')
        try:
            hooks.am_i_primary()
            self.assertFalse(True, "Expected OperationFailure to be raised")
        except OperationFailure:
            mock_run_admin_cmd.assert_called()

    @patch('time.sleep')
    @patch('subprocess.check_output')
    def test_mongo_client_smart_no_command(self, mock_check_output,
                                           mock_sleep):
        rv = hooks.mongo_client_smart()
        self.assertFalse(rv)
        self.assertEqual(0, mock_check_output.call_count)

        mock_check_output.reset_mock()
        mock_check_output.return_value = '{"ok": 1}'

        rv = hooks.mongo_client_smart(command='fake-cmd')
        self.assertTrue(rv)
        mock_check_output.assert_called_once_with(['mongo', '--quiet',
                                                   '--host', 'localhost',
                                                   '--eval',
                                                   'printjson(fake-cmd)'])

    @patch('time.sleep')
    @patch('subprocess.check_output')
    def test_mongo_client_smart_error_cases(self, mock_ck_output, mock_sleep):
        mock_ck_output.side_effect = [CalledProcessError(1, 'cmd',
                                                         output='fake-error')
                                      for x in xrange(11)]
        rv = hooks.mongo_client_smart(command='fake-cmd')
        self.assertFalse(rv)

    @patch('subprocess.call')
    def test_mongo_client(self, mock_subprocess):
        rv = hooks.mongo_client()
        self.assertFalse(rv)
        self.assertEqual(0, mock_subprocess.call_count)

        mock_subprocess.reset_mock()
        rv = hooks.mongo_client(host='fake-host')
        self.assertFalse(rv)
        self.assertEqual(0, mock_subprocess.call_count)

        mock_subprocess.reset_mock()
        rv = hooks.mongo_client(command='fake-command')
        self.assertFalse(rv)
        self.assertEqual(0, mock_subprocess.call_count)

        mock_subprocess.reset_mock()
        mock_subprocess.return_value = 0
        rv = hooks.mongo_client(host='fake-host', command='fake-command')
        expected_cmd = ("mongo --host %s --eval 'printjson(%s)'"
                        % ('fake-host', 'fake-command'))
        mock_subprocess.assert_called_once_with(expected_cmd, shell=True)
        self.assertTrue(rv)

        mock_subprocess.reset_mock()
        mock_subprocess.return_value = 1
        rv = hooks.mongo_client(host='fake-host', command='fake-command')
        expected_cmd = ("mongo --host %s --eval 'printjson(%s)'"
                        % ('fake-host', 'fake-command'))
        mock_subprocess.assert_called_once_with(expected_cmd, shell=True)
        self.assertFalse(rv)

    @patch.object(hooks, 'am_i_primary')
    @patch.object(hooks, 'init_replset')
    @patch.object(hooks, 'relation_get')
    @patch.object(hooks, 'peer_units')
    @patch.object(hooks, 'oldest_peer')
    @patch.object(hooks, 'join_replset')
    @patch.object(hooks, 'unit_get')
    def test_replica_set_relation_changed(self, mock_unit_get,
                                          mock_join_replset, mock_oldest_peer,
                                          mock_peer_units, mock_relation_get,
                                          mock_init_replset, mock_is_primary):
        # set the unit_get('private-address')
        mock_unit_get.return_value = 'juju-local-unit-0.local'
        mock_relation_get.return_value = None

        # Test when remote hostname is None, should not join
        hooks.replica_set_relation_changed()
        self.assertEqual(0, mock_join_replset.call_count)

        # Test remote hostname is valid, but master is somehow not defined
        mock_join_replset.reset_mock()
        mock_relation_get.return_value = 'juju-local-unit-0'

        hooks.replica_set_relation_changed()

        self.assertEqual(1, mock_join_replset.call_count)

        # Test when not oldest peer, don't init replica set
        mock_init_replset.reset_mock()
        mock_oldest_peer.reset_mock()
        mock_peer_units.return_value = ['mongodb/1', 'mongodb/2']
        mock_oldest_peer.return_value = False

        hooks.replica_set_relation_changed()

        self.assertEqual(mock_init_replset.call_count, 0)

        # Test when its also the PRIMARY
        mock_relation_get.reset_mock()
        mock_relation_get.side_effect = ['juju-remote-unit-0', '12345']
        mock_oldest_peer.reset_mock()
        mock_oldest_peer.return_value = False
        mock_is_primary.reset_mock()
        mock_is_primary.return_value = True

        hooks.replica_set_relation_changed()
        call1 = call('juju-local-unit-0.local:27017',
                     'juju-remote-unit-0:12345')
        mock_join_replset.assert_has_calls(call1)

    @patch.object(hooks, 'unit_get')
    @patch.object(hooks, 'leave_replset')
    @patch.object(hooks, 'am_i_primary')
    def test_replica_set_relation_departed(self, mock_am_i_primary,
                                           mock_leave_replset, mock_unit_get):
        mock_am_i_primary.return_value = False
        hooks.replica_set_relation_departed()

        self.assertEqual(0, mock_leave_replset.call_count)

        mock_am_i_primary.reset_mock()
        mock_am_i_primary.return_value = True
        mock_unit_get.return_value = 'juju-local'

        self.test_relation.set({'hostname': 'juju-remote',
                                'port': '27017'})
        mock_leave_replset.reset_mock()

        hooks.replica_set_relation_departed()

        call1 = call('juju-local:27017', 'juju-remote:27017')
        mock_leave_replset.assert_has_calls(call1)
