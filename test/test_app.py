import unittest
import logging
from unittest.mock import patch, ANY

from ecs_scheduler.app import create


@patch('atexit.register')
@patch('werkzeug.serving.is_running_from_reloader')
@patch('ecs_scheduler.app.scheduld.create')
@patch('ecs_scheduler.app.webapi')
@patch('ecs_scheduler.app.datacontext.Jobs')
@patch('ecs_scheduler.app.operations.DirectQueue')
@patch('ecs_scheduler.app.env')
class CreateTests(unittest.TestCase):
    def test_runs_setup_in_prod_mode(self, env, queue_class, datacontext, webapi, create_scheduld, reloader, exit_register):
        reloader.return_value = False
        webapi.create.return_value.debug = False

        result = create()

        env.init.assert_called_with()
        queue_class.assert_called_with()
        datacontext.load.assert_called_with()
        create_scheduld.assert_called_with(queue_class.return_value, datacontext.load.return_value)
        webapi.setup.assert_called_with(webapi.create.return_value, queue_class.return_value, datacontext.load.return_value)
        create_scheduld.return_value.start.assert_called_with()
        exit_register.assert_called_with(ANY, create_scheduld.return_value)
        self.assertIs(webapi.create.return_value, result)

    def test_runs_setup_in_reloader(self, env, queue_class, datacontext, webapi, create_scheduld, reloader, exit_register):
        reloader.return_value = True
        webapi.create.return_value.debug = True

        result = create()

        env.init.assert_called_with()
        queue_class.assert_called_with()
        datacontext.load.assert_called_with()
        create_scheduld.assert_called_with(queue_class.return_value, datacontext.load.return_value)
        webapi.setup.assert_called_with(webapi.create.return_value, queue_class.return_value, datacontext.load.return_value)
        create_scheduld.return_value.start.assert_called_with()
        exit_register.assert_called_with(ANY, create_scheduld.return_value)
        self.assertIs(webapi.create.return_value, result)

    def test_skips_setup_if_debug_and_not_reloader(self, env, queue_class, datacontext, webapi, create_scheduld, reloader, exit_register):
        reloader.return_value = False
        webapi.create.return_value.debug = True

        result = create()

        env.init.assert_called_with()
        queue_class.assert_not_called()
        datacontext.load.assert_not_called()
        create_scheduld.assert_not_called()
        webapi.setup.assert_not_called()
        create_scheduld.return_value.start.assert_not_called()
        exit_register.assert_not_called()
        self.assertIs(webapi.create.return_value, result)

    @patch.object(logging.getLogger('ecs_scheduler.app'), 'critical')
    def test_logs_exceptions(self, fake_log, env, queue_class, datacontext, webapi, create_scheduld, reloader, exit_register):
        env.init.side_effect = RuntimeError

        with self.assertRaises(RuntimeError):
            create()

        fake_log.assert_called()
