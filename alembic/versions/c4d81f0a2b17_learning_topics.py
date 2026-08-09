"""Add learning topics, prerequisites, and per-topic progress

Revision ID: c4d81f0a2b17
Revises: b7e2f4a91c03
Create Date: 2026-08-08 00:00:00.000000

Backs the math/English topic spine. Run
`python -m app.seed.seed_taxonomy` after upgrading to populate the tables;
until then math/English fall back to the old age-bucketed random rotation.
"""
from alembic import op
import sqlalchemy as sa


revision = 'c4d81f0a2b17'
down_revision = 'b7e2f4a91c03'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'learning_topics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('topic_key', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('topic_type', sa.String(), nullable=True),
        sa.Column('age_start', sa.Integer(), nullable=False),
        sa.Column('age_end', sa.Integer(), nullable=False),
        sa.Column('centrality', sa.Float(), server_default='0'),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('assessment_prompt', sa.Text(), nullable=True),
        sa.Column('question_mode', sa.String(), nullable=True),
    )
    op.create_index('ix_learning_topics_id', 'learning_topics', ['id'])
    op.create_index('ix_learning_topics_topic_key', 'learning_topics', ['topic_key'], unique=True)
    op.create_index('ix_learning_topics_subject', 'learning_topics', ['subject'])
    op.create_index('ix_learning_topics_question_mode', 'learning_topics', ['question_mode'])
    op.create_index(
        'ix_learning_topics_subject_ages', 'learning_topics',
        ['subject', 'age_start', 'age_end'],
    )

    op.create_table(
        'topic_prerequisites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('topic_key', sa.String(), nullable=False),
        sa.Column('prerequisite_key', sa.String(), nullable=False),
        sa.Column('strength', sa.String(), nullable=False, server_default='hard'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.UniqueConstraint('topic_key', 'prerequisite_key', name='uq_topic_prereq'),
    )
    op.create_index('ix_topic_prerequisites_id', 'topic_prerequisites', ['id'])
    op.create_index('ix_topic_prerequisites_topic_key', 'topic_prerequisites', ['topic_key'])
    op.create_index(
        'ix_topic_prerequisites_prerequisite_key', 'topic_prerequisites', ['prerequisite_key'],
    )

    op.create_table(
        'user_topic_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('topic_id', sa.Integer(), sa.ForeignKey('learning_topics.id'), nullable=False),
        sa.Column('mastery_score', sa.Integer(), server_default='0'),
        sa.Column('correct_count', sa.Integer(), server_default='0'),
        sa.Column('wrong_count', sa.Integer(), server_default='0'),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('easiness_factor', sa.Float(), server_default='2.5'),
        sa.Column('sm2_interval', sa.Integer(), server_default='0'),
        sa.Column('sm2_repetitions', sa.Integer(), server_default='0'),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.UniqueConstraint('user_id', 'topic_id', name='uq_user_topic'),
    )
    op.create_index('ix_user_topic_progress_id', 'user_topic_progress', ['id'])

    # Batch mode: SQLite cannot ALTER a table to add a foreign key, so alembic
    # recreates the table there. Postgres takes the plain ALTER path.
    with op.batch_alter_table('session_questions') as batch:
        batch.add_column(sa.Column('topic_id', sa.Integer(), nullable=True))
        batch.create_foreign_key(
            'fk_session_questions_topic_id', 'learning_topics', ['topic_id'], ['id'],
        )


def downgrade():
    with op.batch_alter_table('session_questions') as batch:
        batch.drop_constraint('fk_session_questions_topic_id', type_='foreignkey')
        batch.drop_column('topic_id')
    op.drop_table('user_topic_progress')
    op.drop_table('topic_prerequisites')
    op.drop_table('learning_topics')
