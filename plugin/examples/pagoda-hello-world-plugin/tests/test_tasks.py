"""
Tests for Hello World Plugin Celery tasks
"""

import inspect
from unittest.mock import Mock, call, patch

from django.test import TestCase


class TestHelloWorldTask(TestCase):
    """Test cases for hello_world_task"""

    @patch("pagoda_hello_world_plugin.tasks.Job")
    def test_task_execution_success(self, mock_job_class):
        """Test successful task execution"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job

        hello_world_task(1)

        mock_job_class.objects.get.assert_called_once_with(id=1)
        mock_job.is_canceled.assert_called_once()
        mock_job.proceed_if_ready.assert_called_once()
        mock_job.update.assert_called()

    @patch("pagoda_hello_world_plugin.tasks.Job")
    def test_task_job_not_found(self, mock_job_class):
        """Test task execution when Job is not found"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job_class.DoesNotExist = Exception
        mock_job_class.objects.get.side_effect = mock_job_class.DoesNotExist()

        hello_world_task(999)

        mock_job_class.objects.get.assert_called_once_with(id=999)

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_handles_cancellation(self, mock_job_status, mock_job_class):
        """Test that task handles job cancellation"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = True
        mock_job_class.objects.get.return_value = mock_job

        hello_world_task(1)

        mock_job.is_canceled.assert_called_once()
        mock_job.update.assert_not_called()

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_checks_readiness(self, mock_job_status, mock_job_class):
        """Test that task checks job readiness"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = False
        mock_job_class.objects.get.return_value = mock_job

        hello_world_task(1)

        mock_job.proceed_if_ready.assert_called_once()
        mock_job.update.assert_not_called()

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_updates_status_processing(self, mock_job_status, mock_job_class):
        """Test that task updates job status to PROCESSING"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job
        mock_job_status.PROCESSING = 5

        hello_world_task(1)

        calls = [call[0][0] for call in mock_job.update.call_args_list]
        self.assertIn(5, calls)

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_updates_status_done(self, mock_job_status, mock_job_class):
        """Test that task updates job status to DONE on success"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job
        mock_job_status.PROCESSING = 5
        mock_job_status.DONE = 2

        hello_world_task(1)

        last_call = mock_job.update.call_args_list[-1]
        self.assertEqual(last_call[0][0], 2)

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_error_handling(self, mock_job_status, mock_job_class):
        """Test error handling in task execution"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job.update.side_effect = [None, Exception("Update error"), None]
        mock_job_class.objects.get.return_value = mock_job
        mock_job_status.PROCESSING = 5
        mock_job_status.ERROR = 3

        hello_world_task(1)

        error_update_called = any(call[0][0] == 3 for call in mock_job.update.call_args_list)
        self.assertTrue(error_update_called)

    @patch("pagoda_hello_world_plugin.tasks.Job")
    def test_task_with_zero_job_id(self, mock_job_class):
        """Test task execution with job_id=0 (edge case)"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 0
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job

        hello_world_task(0)

        mock_job_class.objects.get.assert_called_once_with(id=0)
        mock_job.update.assert_called()

    @patch("pagoda_hello_world_plugin.tasks.Job")
    def test_task_with_negative_job_id(self, mock_job_class):
        """Test task execution with negative job_id (should still query DB)"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job_class.DoesNotExist = Exception
        mock_job_class.objects.get.side_effect = mock_job_class.DoesNotExist()

        hello_world_task(-1)

        mock_job_class.objects.get.assert_called_once_with(id=-1)

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_call_order(self, mock_job_status, mock_job_class):
        """Test that job methods are called in correct order"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job
        mock_job_status.PROCESSING = 5
        mock_job_status.DONE = 2

        hello_world_task(1)

        expected_calls = [
            call(id=1),
        ]
        mock_job_class.objects.get.assert_has_calls(expected_calls)

        assert mock_job.is_canceled.call_count == 1
        assert mock_job.proceed_if_ready.call_count == 1
        assert mock_job.update.call_count == 2

        update_calls = [c[0][0] for c in mock_job.update.call_args_list]
        self.assertEqual(update_calls[0], 5)
        self.assertEqual(update_calls[1], 2)

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_logging_on_success(self, mock_job_status, mock_job_class):
        """Test that task logs appropriate messages on success"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job
        mock_job_status.PROCESSING = 5
        mock_job_status.DONE = 2

        with patch("pagoda_hello_world_plugin.tasks.logger") as mock_logger:
            hello_world_task(1)
            assert mock_logger.info.call_count >= 2

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_large_job_id(self, mock_job_status, mock_job_class):
        """Test task execution with large job_id"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        large_job_id = 999999999
        mock_job = Mock()
        mock_job.id = large_job_id
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job

        hello_world_task(large_job_id)

        mock_job_class.objects.get.assert_called_once_with(id=large_job_id)
        mock_job.update.assert_called()


class TestRegisterPluginJobTaskDecorator(TestCase):
    """Test cases for @register_plugin_job_task decorator"""

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves the function name"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        self.assertEqual(hello_world_task.__name__, "hello_world_task")

    def test_decorator_adds_metadata(self):
        """Test that decorator adds offset metadata to function"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        self.assertTrue(hasattr(hello_world_task, "_offset"))
        self.assertEqual(hello_world_task._offset, 0)

    def test_decorator_preserves_celery_task_attributes(self):
        """Test that decorator preserves Celery task attributes like delay()"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        self.assertTrue(hasattr(hello_world_task, "delay"))
        self.assertTrue(callable(hello_world_task.delay))

    def test_decorator_preserves_function_signature(self):
        """Test that decorator preserves the original function signature"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        sig = inspect.signature(hello_world_task)
        params = list(sig.parameters.keys())
        self.assertIn("job_id", params)

    def test_task_is_callable(self):
        """Test that decorated task is callable"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        self.assertTrue(callable(hello_world_task))

    @patch("pagoda_hello_world_plugin.tasks.Job")
    def test_decorator_does_not_affect_task_execution(self, mock_job_class):
        """Test that decorator doesn't interfere with task execution"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job

        hello_world_task(1)

        mock_job_class.objects.get.assert_called_once()
        mock_job.update.assert_called()

    def test_task_has_app_task_attributes(self):
        """Test that task has Celery app.task attributes"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        self.assertTrue(hasattr(hello_world_task, "apply_async"))
        self.assertTrue(hasattr(hello_world_task, "delay"))
        self.assertTrue(hasattr(hello_world_task, "apply"))


class TestHelloWorldTaskIntegration(TestCase):
    """Integration tests for hello_world_task with Job model"""

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_full_lifecycle(self, mock_job_status, mock_job_class):
        """Test complete task lifecycle"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True
        mock_job_class.objects.get.return_value = mock_job
        mock_job_status.PROCESSING = 5
        mock_job_status.DONE = 2

        hello_world_task(1)

        assert mock_job_class.objects.get.called
        assert mock_job.is_canceled.called
        assert mock_job.proceed_if_ready.called
        update_statuses = [c[0][0] for c in mock_job.update.call_args_list]
        assert 5 in update_statuses
        assert 2 in update_statuses

    @patch("pagoda_hello_world_plugin.tasks.Job")
    @patch("pagoda_hello_world_plugin.tasks.JobStatus")
    def test_task_handles_multiple_exceptions(self, mock_job_status, mock_job_class):
        """Test task handles various exception types"""
        from pagoda_hello_world_plugin.tasks import hello_world_task

        mock_job = Mock()
        mock_job.id = 1
        mock_job.is_canceled.return_value = False
        mock_job.proceed_if_ready.return_value = True

        exception_types = [
            Exception("Generic error"),
            RuntimeError("Runtime error"),
            ValueError("Value error"),
        ]

        for exc in exception_types:
            mock_job.reset_mock()
            mock_job.update.side_effect = [None, exc, None]
            mock_job_class.objects.get.return_value = mock_job
            mock_job_status.PROCESSING = 5
            mock_job_status.ERROR = 3

            hello_world_task(1)

            error_called = any(c[0][0] == 3 for c in mock_job.update.call_args_list)
            assert error_called, f"ERROR status not called for {exc}"
