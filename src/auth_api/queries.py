from sqlalchemy import orm, func, and_

from origin.sql import SqlQuery

from .models import DbUser, DbExternalUser, DbToken, DbLoginRecord


class UserQuery(SqlQuery):
    """
    Query DbUser.
    """
    def _get_base_query(self) -> orm.Query:
        """
        TODO
        """
        return self.session.query(DbUser)

    def has_ssn(self, ssn: str) -> 'UserQuery':
        """
        :param ssn: Social security number, encrypted
        """
        return self.filter(DbUser.ssn == ssn)

    def has_tin(self, tin: str) -> 'UserQuery':
        """
        :param tin:
        """
        return self.filter(DbUser.cvr == tin)


class ExternalUserQuery(SqlQuery):
    """
    Query DbExternalUser.
    """
    def _get_base_query(self) -> orm.Query:
        """
        TODO
        """
        return self.session.query(DbExternalUser)

    def has_external_subject(self, subject: str) -> 'ExternalUserQuery':
        """
        TODO
        """
        return self.filter(DbExternalUser.external_subject == subject)

    def has_identity_provider(self, ip: str) -> 'ExternalUserQuery':
        """
        :param ip: ID/name of Identity Provider
        """
        return self.filter(DbExternalUser.identity_provider == ip)


class LoginRecordQuery(SqlQuery):
    """
    Query DbLoginRecord.
    """
    def _get_base_query(self) -> orm.Query:
        """
        TODO
        """
        return self.session.query(DbLoginRecord)

    def has_subject(self, subject: str) -> 'LoginRecordQuery':
        """
        TODO
        """
        return self.filter(DbLoginRecord.subject == subject)


class TokenQuery(SqlQuery):
    """
    Query DbToken.
    """
    def _get_base_query(self) -> orm.Query:
        """
        TODO
        """
        return self.session.query(DbToken)

    def has_opaque_token(self, opaque_token: str) -> 'TokenQuery':
        """
        TODO
        """
        return self.filter(DbToken.opaque_token == opaque_token)

    def is_valid(self) -> 'TokenQuery':
        """
        TODO
        """
        return self.filter(and_(
            DbToken.issued <= func.now(),
            DbToken.expires > func.now(),
        ))
