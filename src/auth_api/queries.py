from sqlalchemy import orm, func, and_

from origin.sql import SqlQuery

from .models import DbUser, DbExternalUser, DbToken, DbLoginRecord


class UserQuery(SqlQuery):
    """Query DbUser."""

    def _get_base_query(self) -> orm.Query:
        """Override function used in base class."""

        return self.session.query(DbUser)

    def has_ssn(self, ssn: str) -> 'UserQuery':
        """
        Check if the actor's ssn matches a ssn in the database.

        :param ssn: Social security number, encrypted
        """

        return self.filter(DbUser.ssn == ssn)

    def has_tin(self, tin: str) -> 'UserQuery':
        """
        Check if the subject's tin matches a tin in the database.

        :param tin: Tax Identification Number
        """
        return self.filter(DbUser.tin == tin)


class ExternalUserQuery(SqlQuery):
    """Query DbExternalUser."""

    def _get_base_query(self) -> orm.Query:
        """Override function used in base class."""

        return self.session.query(DbExternalUser)

    def has_external_subject(self, subject: str) -> 'ExternalUserQuery':
        """
        Check if the external subject exists in the database.

        :param subject: ID/Name of the external subject
        """

        return self.filter(DbExternalUser.external_subject == subject)

    def has_identity_provider(self, idp: str) -> 'ExternalUserQuery':
        """
        Check if the subject has the given identity provider in the database.

        :param idp: ID/name of Identity Provider
        """

        return self.filter(DbExternalUser.identity_provider == idp)


class LoginRecordQuery(SqlQuery):
    """Query DbLoginRecord."""

    def _get_base_query(self) -> orm.Query:
        """Override function used in base class."""

        return self.session.query(DbLoginRecord)

    def has_subject(self, subject: str) -> 'LoginRecordQuery':
        """
        Check if the subject exists in the database.

        param subject: ID/Name of the subject
        """

        return self.filter(DbLoginRecord.subject == subject)


class TokenQuery(SqlQuery):
    """Query DbToken."""

    def _get_base_query(self) -> orm.Query:
        """Override function used in base class."""

        return self.session.query(DbToken)

    def has_opaque_token(self, opaque_token: str) -> 'TokenQuery':
        """
        Check if the opaque token exists in the database.

        param opaque_token: Primary Key Constraint
        """

        return self.filter(DbToken.opaque_token == opaque_token)

    def is_valid(self) -> 'TokenQuery':
        """Check if the token has a correct issued and expires datetime."""

        return self.filter(and_(
            DbToken.issued <= func.now(),
            DbToken.expires > func.now(),
        ))
