"""Initial database schema

Revision ID: initial
Revises: 
Create Date: 2026-01-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = 'initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('failed_login_attempts', sa.Integer, default=0, nullable=False),
        sa.Column('locked_until', sa.DateTime, nullable=True),
        sa.Column('must_change_password', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create files table
    op.create_table(
        'files',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False, index=True),
        sa.Column('filepath', sa.String(500), nullable=False),
        sa.Column('size', sa.BigInteger, nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('uploaded_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('upload_date', sa.DateTime, nullable=False, index=True),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('sync_status', sa.Enum('pending', 'synced', 'conflict', 'error', name='syncstatus'), nullable=False)
    )
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('token', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False, index=True)
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('target_file_id', UUID(as_uuid=True), sa.ForeignKey('files.id'), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True)
    )
    
    # Create scheduled_tasks table
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('task_name', sa.String(100), unique=True, nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('cron_expression', sa.String(50), nullable=False),
        sa.Column('is_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('last_run_at', sa.DateTime, nullable=True),
        sa.Column('last_run_status', sa.Enum('success', 'failed', 'running', 'cancelled', name='taskstatus'), nullable=True),
        sa.Column('next_run_at', sa.DateTime, nullable=True, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create task_execution_history table
    op.create_table(
        'task_execution_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('scheduled_tasks.id'), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.Enum('success', 'failed', 'running', 'cancelled', name='taskstatus'), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('triggered_by', sa.String(50), nullable=False)
    )
    
    # Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('sync_type', sa.Enum('win_to_ubuntu', 'ubuntu_to_win', name='synctype'), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('files_synced', sa.Integer, default=0, nullable=False),
        sa.Column('bytes_transferred', sa.BigInteger, default=0, nullable=False),
        sa.Column('status', sa.Enum('success', 'failed', 'partial', 'running', name='synclogstatus'), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True)
    )
    
    # Create upload_chunks table
    op.create_table(
        'upload_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('upload_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('total_chunks', sa.Integer, nullable=False),
        sa.Column('chunk_number', sa.Integer, nullable=False),
        sa.Column('chunk_size', sa.BigInteger, nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('uploaded_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False)
    )
    
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('value', JSONB, nullable=False),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )


def downgrade() -> None:
    op.drop_table('system_settings')
    op.drop_table('upload_chunks')
    op.drop_table('sync_logs')
    op.drop_table('task_execution_history')
    op.drop_table('scheduled_tasks')
    op.drop_table('audit_logs')
    op.drop_table('sessions')
    op.drop_table('files')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS syncstatus')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS synctype')
    op.execute('DROP TYPE IF EXISTS synclogstatus')
