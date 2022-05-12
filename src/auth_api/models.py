# Third party
import sqlalchemy as sa
from sqlalchemy.orm import relationship

# Local
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
        sa.CheckConstraint('ssn != NULL OR tin != null'),
    )

    subject = sa.Column(sa.String(), index=True, nullable=False)
    """The user subject used to identify users."""

    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())
    """Time the user was created."""

    ssn = sa.Column(sa.String(), index=True)
    """Social security number, encrypted."""

    tin = sa.Column(sa.String(), index=True)
    """Tax identification number."""

class DbCompany(db.ModelBase):
    """
    Represents a user logging in the system.

    Users are uniquely identified by their subject.
    """

    __tablename__ = 'company'
    __table_args__ = (
        sa.PrimaryKeyConstraint('subject'),
        sa.UniqueConstraint('subject'),
        sa.UniqueConstraint('tin'),
        sa.CheckConstraint('tin != null'),
    )

    id = sa.Column(sa.String(), index=True, nullable=False)
    """Unique id for the Database record."""

    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())
    """Time the company was created."""

    tin = sa.Column(sa.String(), index=True, nullable=False)
    """Tax identification number."""

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
    """Unique id for the Database record."""

    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())
    """Time when the user signed up using identity provider."""

    subject = sa.Column(sa.String(), sa.ForeignKey(
        'user.subject'), index=True, nullable=False)

    identity_provider = sa.Column(sa.String(), index=True, nullable=False)
    """ID/name of Identity Provider."""

    external_subject = sa.Column(sa.String(), index=True, nullable=False)
    """
    Identity Provider's unique ID of the user.

    The identity provider must have their own unique ID of their
    users. This will not be the same as ours therefor we'll save this in order
    to link other users with the external identity provider.
    """

    # Relationships
    user = relationship('DbUser', foreign_keys=[subject], uselist=False)


class DbLoginRecord(db.ModelBase):
    """
    Database login record.

    A database that store the users who logged in a the current time.
    The user is identified by the subject.
    """

    __tablename__ = 'login_record'
    __table_args__ = (
        sa.PrimaryKeyConstraint('id'),
    )

    id = sa.Column(sa.Integer(), index=True)
    """Unique id for the Database record."""

    subject = sa.Column(sa.String(), index=True, nullable=False)
    """The user subject used to identify users."""

    created = sa.Column(sa.DateTime(timezone=True),
                        nullable=False, server_default=sa.func.now())
    """Time when the user logged in."""


class DbToken(db.ModelBase):
    """
    Contains the user sessions.

    Each session contains two tokens, internal_token for internal use and
    id_token used to make requests to the used
    identity provider(MitID, Nemid, etc). The tokens are assigned to a specific
    user using the user "subject".
    """

    __tablename__ = 'token'
    __table_args__ = (
        sa.PrimaryKeyConstraint('opaque_token'),
        sa.UniqueConstraint('opaque_token'),
        sa.CheckConstraint('issued < expires'),
    )

    opaque_token = sa.Column(sa.String(), index=True, nullable=False)
    """
    Opaque token which is safe to pass to the frontend clients

    This token is nothing but a unique id and contains no
    information in itself. This is used to exchange it for a internal token,
    which happens at the reverse proxy level in a middleware,
    using the ForwardAuth endpoint.
    """

    internal_token = sa.Column(sa.String(), nullable=False)
    """Internal token used by our own system"""

    id_token = sa.Column(sa.String(), nullable=False)
    """Token used by identity provider"""

    issued = sa.Column(sa.DateTime(timezone=True), nullable=False)
    """Time when token were issued"""

    expires = sa.Column(sa.DateTime(timezone=True), nullable=False)
    """Time when token expired"""

    subject = sa.Column(sa.String(), index=True, nullable=False)
    """Unique subject which identifies the user"""
