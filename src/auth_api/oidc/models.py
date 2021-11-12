from datetime import datetime
from abc import abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class OpenIDConnectToken:
    """
    Abstracts away lower-level structure of OpenID Connect ID tokens
    under a single interface to make it easy to switch OpenID Connect
    backends without it having any effect on clients depending on it.
    """

    @property
    @abstractmethod
    def issued(self) -> datetime:
        """
        TODO
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def expires(self) -> datetime:
        """
        Time of expiration.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def subject(self) -> str:
        """
        User unique subject (ID) for this provider.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def provider(self) -> str:
        """
        Name of identity provider (ie. 'mitid' or 'nemid' etc).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def scope(self) -> List[str]:
        """
        Scopes granted in this token.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def id_token(self) -> str:
        """
        id_token encoded (raw).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def is_private(self) -> bool:
        """
        Whether or not this is a privat person.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def is_company(self) -> bool:
        """
        Whether or not this is a company.
        """
        raise NotImplementedError

    # -- For private persons only --------------------------------------------

    @property
    @abstractmethod
    def ssn(self) -> Optional[str]:
        """
        Social security number (for private persons).
        """
        raise NotImplementedError

    # -- For companies only --------------------------------------------------

    @property
    @abstractmethod
    def tin(self) -> Optional[str]:
        """
        Tax identification number (for companies).
        """
        raise NotImplementedError
