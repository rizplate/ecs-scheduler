import unittest
import logging
import os
from unittest.mock import patch, ANY

from ecs_scheduler.app import create


@patch('atexit.register')
@patch('werkzeug.serving.is_running_from_reloader')
@patch('ecs_scheduler.scheduld.create')
@patch('ecs_scheduler.webapi.create')
@patch('ecs_scheduler.app.jobtasks.SqsTaskQueue')
@patch('ecs_scheduler.app.init')
class CreateTests(unittest.TestCase):
    def test_starts_daemon_in_prod_mode(self, fake_init, fake_queue_class, create_webapi, create_scheduld, reloader, exit_register):
        fake_init.config.return_value = {'aws': 'foo'}
        reloader.return_value = False
        create_webapi.return_value.debug = False

        result = create()

        fake_init.env.assert_called_with()
        fake_queue_class.assert_called_with('foo')
        create_scheduld.assert_called_with(fake_init.config.return_value)
        create_webapi.assert_called_with(fake_init.config.return_value, fake_queue_class.return_value)
        create_scheduld.return_value.start.assert_called_with()
        exit_register.assert_called_with(ANY, create_scheduld.return_value)
        self.assertIs(create_webapi.return_value, result)

    def test_starts_daemon_in_reloader(self, fake_init, fake_queue_class, create_webapi, create_scheduld, reloader, exit_register):
        fake_init.config.return_value = {'aws': 'foo'}
        reloader.return_value = True
        create_webapi.return_value.debug = True

        result = create()

        fake_init.env.assert_called_with()
        fake_queue_class.assert_called_with('foo')
        create_scheduld.assert_called_with(fake_init.config.return_value)
        create_webapi.assert_called_with(fake_init.config.return_value, fake_queue_class.return_value)
        create_scheduld.return_value.start.assert_called_with()
        exit_register.assert_called_with(ANY, create_scheduld.return_value)
        self.assertIs(create_webapi.return_value, result)

    def test_skips_daemon_if_debug_and_not_reloader(self, fake_init, fake_queue_class, create_webapi, create_scheduld, reloader, exit_register):
        fake_init.config.return_value = {'aws': 'foo'}
        reloader.return_value = False
        create_webapi.return_value.debug = True

        result = create()

        fake_init.env.assert_called_with()
        fake_queue_class.assert_called_with('foo')
        create_scheduld.assert_not_called()
        create_webapi.assert_called_with(fake_init.config.return_value, fake_queue_class.return_value)
        create_scheduld.return_value.start.assert_not_called()
        exit_register.assert_not_called()
        self.assertIs(create_webapi.return_value, result)

    @patch.object(logging.getLogger('ecs_scheduler.app'), 'critical')
    def test_startup_logs_exceptions(self, fake_log, fake_init, fake_queue_class, create_webapi, create_scheduld, reloader, exit_register):
        fake_init.config.side_effect = RuntimeError

        with self.assertRaises(RuntimeError):
            create()

        fake_log.assert_called()
