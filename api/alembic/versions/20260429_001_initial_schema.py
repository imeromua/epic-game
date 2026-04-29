"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== players ====================
    op.create_table(
        'players',
        sa.Column('id',                   sa.Integer(),    primary_key=True),
        sa.Column('tg_id',                sa.BigInteger(), nullable=False),
        sa.Column('tg_username',          sa.String(64)),
        sa.Column('name',                 sa.String(128),  nullable=False),
        sa.Column('phone',                sa.String(20)),
        sa.Column('xp',                   sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('xp_total',             sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('rank',
            sa.Enum('newbie','scout','expert','master','legend', name='playerrank'),
            nullable=False, server_default='newbie'),
        sa.Column('streak',               sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('streak_max',           sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('quests_won',           sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('quests_participated',  sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('legendary_wins',       sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('is_admin',             sa.Boolean(),    nullable=False, server_default='false'),
        sa.Column('is_active',            sa.Boolean(),    nullable=False, server_default='true'),
        sa.Column('last_active_at',       sa.DateTime(timezone=True)),
        sa.Column('created_at',           sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_players_tg_id', 'players', ['tg_id'], unique=True)

    # ==================== prizes ====================
    op.create_table(
        'prizes',
        sa.Column('id',                  sa.Integer(),   primary_key=True),
        sa.Column('name',                sa.String(128), nullable=False),
        sa.Column('description',         sa.Text()),
        sa.Column('emoji',               sa.String(8),   nullable=False, server_default='🎁'),
        sa.Column('category',
            sa.Enum('1','2','3','4', name='prizecategory'),
            nullable=False),
        sa.Column('prize_type',
            sa.Enum('material','non_material','xp_shop', name='prizetype'),
            nullable=False, server_default='material'),
        sa.Column('weight',              sa.Integer(),   nullable=False, server_default='30'),
        sa.Column('cost_uah',            sa.Integer(),   nullable=False, server_default='0'),
        sa.Column('xp_cost',             sa.Integer(),   nullable=False, server_default='0'),
        sa.Column('stock',               sa.Integer()),
        sa.Column('stock_monthly_limit', sa.Integer()),
        sa.Column('is_active',           sa.Boolean(),   nullable=False, server_default='true'),
        sa.Column('is_rare',             sa.Boolean(),   nullable=False, server_default='false'),
        sa.Column('created_at',          sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # ==================== quests ====================
    op.create_table(
        'quests',
        sa.Column('id',                 sa.Integer(),   primary_key=True),
        sa.Column('title',              sa.String(256), nullable=False),
        sa.Column('description',        sa.Text(),      nullable=False),
        sa.Column('category',
            sa.Enum('1','2','3','4', name='questcategory'),
            nullable=False),
        sa.Column('quest_type',
            sa.Enum('photo','text','choice', name='questtype'),
            nullable=False),
        sa.Column('correct_answer',     sa.Text()),
        sa.Column('answer_options',     sa.Text()),
        sa.Column('time_limit_minutes', sa.Integer(),   nullable=False, server_default='5'),
        sa.Column('xp_reward',          sa.Integer(),   nullable=False),
        sa.Column('xp_participation',   sa.Integer(),   nullable=False, server_default='10'),
        sa.Column('prize_id',           sa.Integer(),   sa.ForeignKey('prizes.id')),
        sa.Column('status',
            sa.Enum('pending','active','closed','expired','cancelled', name='queststatus'),
            nullable=False, server_default='pending'),
        sa.Column('scheduled_at',       sa.DateTime(timezone=True)),
        sa.Column('started_at',         sa.DateTime(timezone=True)),
        sa.Column('closed_at',          sa.DateTime(timezone=True)),
        sa.Column('tg_message_id',      sa.BigInteger()),
        sa.Column('announce_30min',     sa.Boolean(),   nullable=False, server_default='false'),
        sa.Column('announce_5min',      sa.Boolean(),   nullable=False, server_default='false'),
        sa.Column('announce_text_30',   sa.Text()),
        sa.Column('announce_text_5',    sa.Text()),
        sa.Column('is_template',        sa.Boolean(),   nullable=False, server_default='false'),
        sa.Column('template_name',      sa.String(128)),
        sa.Column('created_by',         sa.Integer()),
        sa.Column('created_at',         sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_quests_status',      'quests', ['status'])
    op.create_index('ix_quests_is_template', 'quests', ['is_template'])
    op.create_index('ix_quests_scheduled',   'quests', ['scheduled_at'])

    # ==================== quest_results ====================
    op.create_table(
        'quest_results',
        sa.Column('id',               sa.Integer(), primary_key=True),
        sa.Column('quest_id',         sa.Integer(), sa.ForeignKey('quests.id',  ondelete='CASCADE'), nullable=False),
        sa.Column('player_id',        sa.Integer(), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_winner',        sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('answer_text',      sa.Text()),
        sa.Column('photo_file_id',    sa.String(256)),
        sa.Column('photo_hash',       sa.String(64)),
        sa.Column('time_to_win',      sa.Interval()),
        sa.Column('xp_earned',        sa.Integer(), nullable=False, server_default='0'),
        sa.Column('photo_validated',  sa.Boolean()),
        sa.Column('validated_by',     sa.Integer()),
        sa.Column('validated_at',     sa.DateTime(timezone=True)),
        sa.Column('submitted_at',     sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_qr_player',  'quest_results', ['player_id'])
    op.create_index('ix_qr_quest',   'quest_results', ['quest_id'])
    op.create_index('ix_qr_winner',  'quest_results', ['is_winner'])

    # ==================== prize_transactions ====================
    op.create_table(
        'prize_transactions',
        sa.Column('id',           sa.Integer(),   primary_key=True),
        sa.Column('player_id',    sa.Integer(),   sa.ForeignKey('players.id'), nullable=False),
        sa.Column('prize_id',     sa.Integer(),   sa.ForeignKey('prizes.id'),  nullable=False),
        sa.Column('quest_id',     sa.Integer(),   sa.ForeignKey('quests.id')),
        sa.Column('qr_token',     sa.String(64),  unique=True, nullable=False),
        sa.Column('qr_expires_at',sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_issued',    sa.Boolean(),   nullable=False, server_default='false'),
        sa.Column('issued_by',    sa.Integer(),   sa.ForeignKey('players.id')),
        sa.Column('issued_at',    sa.DateTime(timezone=True)),
        sa.Column('source',       sa.String(32),  nullable=False, server_default='quest'),
        sa.Column('created_at',   sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_pt_player', 'prize_transactions', ['player_id'])


def downgrade() -> None:
    op.drop_table('prize_transactions')
    op.drop_table('quest_results')
    op.drop_table('quests')
    op.drop_table('prizes')
    op.drop_table('players')

    # Drop enums
    for e in ('playerrank','prizecategory','prizetype','questcategory','questtype','queststatus'):
        sa.Enum(name=e).drop(op.get_bind(), checkfirst=True)
