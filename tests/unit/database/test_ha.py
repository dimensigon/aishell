"""
Comprehensive tests for High Availability and Disaster Recovery

Tests replication setup, failover scenarios, primary/replica switching,
and point-in-time recovery.
"""

import pytest
from datetime import datetime, timedelta
from src.database.ha import (
    ReplicationNode,
    ReplicationManager,
    FailoverManager,
    RecoveryManager
)


class TestReplicationNode:
    """Test ReplicationNode dataclass."""

    def test_node_creation(self):
        """Test creating replication node."""
        node = ReplicationNode(
            node_id="primary",
            connection_string="postgresql://localhost:5432/db",
            role="primary"
        )

        assert node.node_id == "primary"
        assert node.connection_string == "postgresql://localhost:5432/db"
        assert node.role == "primary"
        assert node.status == "unknown"
        assert node.last_check is None
        assert node.lag_seconds == 0.0

    def test_node_with_status(self):
        """Test node with custom status."""
        now = datetime.now()
        node = ReplicationNode(
            node_id="replica_1",
            connection_string="postgresql://replica:5432/db",
            role="replica",
            status="active",
            last_check=now,
            lag_seconds=0.5
        )

        assert node.status == "active"
        assert node.last_check == now
        assert node.lag_seconds == 0.5


class TestReplicationManager:
    """Test ReplicationManager class."""

    def test_manager_initialization(self):
        """Test replication manager initialization."""
        manager = ReplicationManager()

        assert manager._nodes == {}
        assert manager._primary is None
        assert manager._replicas == []

    def test_setup_replication(self):
        """Test setting up replication."""
        manager = ReplicationManager()

        result = manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[
                "postgresql://replica1:5432/db",
                "postgresql://replica2:5432/db"
            ]
        )

        assert result['status'] == 'success'
        assert result['primary'] == 'primary'
        assert len(result['replicas']) == 2
        assert 'replica_1' in result['replicas']
        assert 'replica_2' in result['replicas']

    def test_setup_creates_nodes(self):
        """Test setup creates primary and replica nodes."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        assert 'primary' in manager._nodes
        assert manager._nodes['primary'].role == 'primary'
        assert manager._nodes['primary'].status == 'active'

        assert 'replica_1' in manager._nodes
        assert manager._nodes['replica_1'].role == 'replica'
        assert manager._nodes['replica_1'].status == 'active'

    def test_setup_multiple_replicas(self):
        """Test setup with multiple replicas."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[
                "postgresql://replica1:5432/db",
                "postgresql://replica2:5432/db",
                "postgresql://replica3:5432/db"
            ]
        )

        assert len(manager._replicas) == 3
        assert 'replica_1' in manager._replicas
        assert 'replica_2' in manager._replicas
        assert 'replica_3' in manager._replicas


class TestReplicationStatus:
    """Test replication status monitoring."""

    def test_get_replication_status(self):
        """Test getting replication status."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        status = manager.get_replication_status()

        assert status['primary'] is not None
        assert status['primary']['role'] == 'primary'
        assert len(status['replicas']) == 1
        assert status['total_nodes'] == 2
        assert status['healthy_nodes'] == 2

    def test_status_includes_node_info(self):
        """Test status includes node information."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        status = manager.get_replication_status()

        primary_info = status['primary']
        assert primary_info['node_id'] == 'primary'
        assert primary_info['role'] == 'primary'
        assert primary_info['status'] == 'active'
        assert primary_info['lag_seconds'] == 0.0

    def test_status_with_no_replication(self):
        """Test status with no replication setup."""
        manager = ReplicationManager()

        status = manager.get_replication_status()

        assert status['primary'] is None
        assert status['replicas'] == []
        assert status['total_nodes'] == 0
        assert status['healthy_nodes'] == 0


class TestReplicationLag:
    """Test replication lag monitoring."""

    def test_check_replication_lag(self):
        """Test checking replication lag."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        lag = manager.check_replication_lag('replica_1')

        assert lag == 0.5  # Mock lag value
        assert manager._nodes['replica_1'].lag_seconds == 0.5

    def test_check_lag_for_primary(self):
        """Test checking lag for primary returns 0."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[]
        )

        lag = manager.check_replication_lag('primary')

        assert lag == 0.0

    def test_check_lag_for_non_existent_node(self):
        """Test checking lag for non-existent node."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[]
        )

        lag = manager.check_replication_lag('non_existent')

        assert lag == 0.0

    def test_lag_updates_last_check(self):
        """Test lag check updates last_check timestamp."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        before = datetime.now()
        manager.check_replication_lag('replica_1')
        after = datetime.now()

        last_check = manager._nodes['replica_1'].last_check

        assert last_check is not None
        assert before <= last_check <= after


class TestReplicaPromotion:
    """Test replica promotion to primary."""

    def test_promote_replica(self):
        """Test promoting replica to primary."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        result = manager.promote_replica('replica_1')

        assert result['status'] == 'success'
        assert result['new_primary'] == 'replica_1'
        assert 'promoted_at' in result

    def test_promotion_updates_roles(self):
        """Test promotion updates node roles."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        manager.promote_replica('replica_1')

        assert manager._nodes['replica_1'].role == 'primary'
        assert manager._primary == 'replica_1'
        assert 'replica_1' not in manager._replicas

    def test_promotion_demotes_old_primary(self):
        """Test promotion demotes old primary."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        manager.promote_replica('replica_1')

        assert manager._nodes['primary'].role == 'replica'

    def test_promote_non_existent_replica(self):
        """Test promoting non-existent replica."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[]
        )

        result = manager.promote_replica('non_existent')

        assert result['status'] == 'error'
        assert 'not found' in result['message']

    def test_promote_primary_node(self):
        """Test promoting primary node fails."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        result = manager.promote_replica('primary')

        assert result['status'] == 'error'
        assert 'not a replica' in result['message']


class TestFailoverManager:
    """Test FailoverManager class."""

    def test_manager_initialization(self):
        """Test failover manager initialization."""
        manager = FailoverManager()

        assert manager._failed_nodes == []
        assert manager._failover_history == []

    def test_detect_failure(self):
        """Test detecting node failure."""
        manager = FailoverManager()

        result = manager.detect_failure('node_1')

        assert result is True
        assert 'node_1' in manager._failed_nodes

    def test_detect_failure_records_event(self):
        """Test failure detection records event in history."""
        manager = FailoverManager()

        manager.detect_failure('node_1')

        history = manager.get_failover_history()

        assert len(history) == 1
        assert history[0]['event'] == 'failure_detected'
        assert history[0]['node_id'] == 'node_1'

    def test_detect_same_failure_twice(self):
        """Test detecting same failure twice."""
        manager = FailoverManager()

        first = manager.detect_failure('node_1')
        second = manager.detect_failure('node_1')

        assert first is True
        assert second is False  # Already detected

    def test_detect_multiple_failures(self):
        """Test detecting multiple node failures."""
        manager = FailoverManager()

        manager.detect_failure('node_1')
        manager.detect_failure('node_2')
        manager.detect_failure('node_3')

        assert len(manager._failed_nodes) == 3


class TestFailoverExecution:
    """Test failover execution."""

    def test_execute_failover(self):
        """Test executing failover."""
        manager = FailoverManager()

        new_primary = manager.execute_failover()

        assert new_primary == 'replica_1'

    def test_failover_records_event(self):
        """Test failover execution records event."""
        manager = FailoverManager()

        manager.execute_failover()

        history = manager.get_failover_history()

        assert len(history) == 1
        assert history[0]['event'] == 'failover_executed'
        assert history[0]['new_primary'] == 'replica_1'

    def test_failover_after_failure_detection(self):
        """Test complete failover flow."""
        manager = FailoverManager()

        manager.detect_failure('primary')
        new_primary = manager.execute_failover()

        history = manager.get_failover_history()

        assert len(history) == 2
        assert history[0]['event'] == 'failure_detected'
        assert history[1]['event'] == 'failover_executed'


class TestRecoveryManager:
    """Test RecoveryManager class."""

    def test_manager_initialization(self):
        """Test recovery manager initialization."""
        manager = RecoveryManager()

        assert manager._recovery_history == []

    def test_recover_to_point_in_time(self):
        """Test point-in-time recovery."""
        manager = RecoveryManager()

        target_time = datetime.now() - timedelta(hours=1)
        result = manager.recover_to_point_in_time(target_time)

        assert result['status'] == 'success'
        assert result['target_time'] == target_time.isoformat()
        assert result['backup_id'] == 'latest'
        assert 'completed_at' in result

    def test_recovery_with_specific_backup(self):
        """Test recovery with specific backup ID."""
        manager = RecoveryManager()

        target_time = datetime.now()
        result = manager.recover_to_point_in_time(
            target_time,
            backup_id='backup_123'
        )

        assert result['backup_id'] == 'backup_123'

    def test_recovery_records_history(self):
        """Test recovery records in history."""
        manager = RecoveryManager()

        target_time = datetime.now()
        manager.recover_to_point_in_time(target_time)

        history = manager.get_recovery_history()

        assert len(history) == 1
        assert history[0]['status'] == 'success'

    def test_multiple_recoveries(self):
        """Test multiple recovery operations."""
        manager = RecoveryManager()

        for i in range(3):
            target_time = datetime.now() - timedelta(hours=i)
            manager.recover_to_point_in_time(target_time)

        history = manager.get_recovery_history()

        assert len(history) == 3


class TestBackupRestoration:
    """Test backup restoration."""

    def test_restore_from_backup(self):
        """Test restoring from backup."""
        manager = RecoveryManager()

        result = manager.restore_from_backup('backup_123')

        assert result['status'] == 'success'
        assert result['backup_id'] == 'backup_123'
        assert result['target_database'] == 'default'
        assert 'restored_at' in result

    def test_restore_to_specific_database(self):
        """Test restoring to specific database."""
        manager = RecoveryManager()

        result = manager.restore_from_backup(
            'backup_123',
            target_database='test_db'
        )

        assert result['target_database'] == 'test_db'

    def test_restore_includes_timing(self):
        """Test restore includes recovery time."""
        manager = RecoveryManager()

        result = manager.restore_from_backup('backup_123')

        assert 'recovery_time_seconds' in result
        assert result['recovery_time_seconds'] > 0


class TestBackupValidation:
    """Test backup validation."""

    def test_validate_backup(self):
        """Test validating backup integrity."""
        manager = RecoveryManager()

        result = manager.validate_backup('backup_123')

        assert result['backup_id'] == 'backup_123'
        assert result['valid'] is True
        assert 'size_mb' in result
        assert 'checksum' in result

    def test_validation_includes_metadata(self):
        """Test validation includes backup metadata."""
        manager = RecoveryManager()

        result = manager.validate_backup('backup_123')

        assert result['size_mb'] == 1024.5
        assert result['checksum'] == 'a1b2c3d4e5f6'
        assert 'validated_at' in result


class TestCompleteHAScenario:
    """Test complete HA scenario with all components."""

    def test_full_failover_scenario(self):
        """Test complete failover scenario."""
        replication_mgr = ReplicationManager()
        failover_mgr = FailoverManager()

        # Setup replication
        replication_mgr.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[
                "postgresql://replica1:5432/db",
                "postgresql://replica2:5432/db"
            ]
        )

        # Detect primary failure
        failover_mgr.detect_failure('primary')

        # Execute failover
        new_primary = failover_mgr.execute_failover()

        # Promote replica
        result = replication_mgr.promote_replica(new_primary)

        # Verify final state
        assert result['status'] == 'success'
        assert replication_mgr._nodes[new_primary].role == 'primary'

        history = failover_mgr.get_failover_history()
        assert len(history) == 2

    def test_disaster_recovery_scenario(self):
        """Test disaster recovery scenario."""
        recovery_mgr = RecoveryManager()

        # Validate backup
        validation = recovery_mgr.validate_backup('backup_latest')
        assert validation['valid'] is True

        # Restore from backup
        restore = recovery_mgr.restore_from_backup('backup_latest')
        assert restore['status'] == 'success'

        # Point-in-time recovery
        target_time = datetime.now() - timedelta(hours=2)
        pitr = recovery_mgr.recover_to_point_in_time(target_time)
        assert pitr['status'] == 'success'

        # Verify history
        history = recovery_mgr.get_recovery_history()
        assert len(history) == 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_setup_replication_with_no_replicas(self):
        """Test replication setup with no replicas."""
        manager = ReplicationManager()

        result = manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=[]
        )

        assert result['status'] == 'success'
        assert len(result['replicas']) == 0

    def test_failover_with_no_failures(self):
        """Test failover when no failures detected."""
        manager = FailoverManager()

        new_primary = manager.execute_failover()

        assert new_primary is not None

    def test_replication_lag_monitoring_consistency(self):
        """Test replication lag monitoring stays consistent."""
        manager = ReplicationManager()

        manager.setup_replication(
            primary="postgresql://primary:5432/db",
            replicas=["postgresql://replica1:5432/db"]
        )

        lag1 = manager.check_replication_lag('replica_1')
        lag2 = manager.check_replication_lag('replica_1')

        assert lag1 == lag2 == 0.5

    def test_recovery_history_ordering(self):
        """Test recovery history maintains order."""
        manager = RecoveryManager()

        times = []
        for i in range(5):
            target_time = datetime.now() - timedelta(hours=i)
            times.append(target_time)
            manager.recover_to_point_in_time(target_time)

        history = manager.get_recovery_history()

        assert len(history) == 5
        for i, record in enumerate(history):
            assert record['target_time'] == times[i].isoformat()
