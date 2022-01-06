import sqlalchemy as sa
from sqlalchemy.orm import relationship

from .db import db


class DbUser(db.ModelBase):
    """
    Represents a user logging in the system.

    Users are uniquely identified by their subject.
    """
    __tablename__ = 'user'
    __table_args__ = (
        sa.PrimaryKeyConstraint('subject'),
        sa.UniqueConstraint('subject'),
        sa.UniqueConstraint('ssn'),
        sa.CheckConstraint('ssn != NULL OR cvr != null'),
    )

    subject = sa.Column(sa.String(), index=True, nullable=False)
    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())

    # Social security number, encrypted
    ssn = sa.Column(sa.String(), index=True)

    # Social security number, encrypted
    cvr = sa.Column(sa.String(), index=True)  # TODO Rename to 'tin'


class DbExternalUser(db.ModelBase):
    """
    Represents a user logging in via some Identity Provider.

    A single user (represented via the DbUser model) can have multiple logins
    using either different Identity Providers, or using different login method
    via the same Identity Provider (for instance, logging in via MitID or
    NemID results in different user IDs even if its the same person).
    """
    __tablename__ = 'user_external'
    __table_args__ = (
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_provider', 'external_subject'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, index=True)
    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())
    subject = sa.Column(sa.String(), sa.ForeignKey(
        'user.subject'), index=True, nullable=False)

    # ID/name of Identity Provider
    identity_provider = sa.Column(sa.String(), index=True, nullable=False)

    # Identity Provider's ID of the user
    external_subject = sa.Column(sa.String(), index=True, nullable=False)

    # Relationships
    user = relationship('DbUser', foreign_keys=[subject], uselist=False)


class DbLoginRecord(db.ModelBase):
    """
    TODO
    """
    __tablename__ = 'login_record'
    __table_args__ = (
        sa.PrimaryKeyConstraint('id'),
    )

    id = sa.Column(sa.Integer(), index=True)
    subject = sa.Column(sa.String(), index=True, nullable=False)
    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())


class DbToken(db.ModelBase):
    """
    TODO
    """
    __tablename__ = 'token'
    __table_args__ = (
        sa.PrimaryKeyConstraint('opaque_token'),
        sa.UniqueConstraint('opaque_token'),
        sa.CheckConstraint('issued < expires'),
    )

    opaque_token = sa.Column(sa.String(), index=True, nullable=False)
    internal_token = sa.Column(sa.String(), nullable=False)
    id_token = sa.Column(sa.String(), nullable=False)
    issued = sa.Column(sa.DateTime(timezone=True), nullable=False)
    expires = sa.Column(sa.DateTime(timezone=True), nullable=False)
    subject = sa.Column(sa.String(), index=True, nullable=False)
