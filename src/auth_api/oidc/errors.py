
# Errors from Identity Provider translates into these errors codes
# as an internal abstraction over OpenID Connect errors.

OIDC_ERROR_CODES = {

    'E0': 'Unknown error from Identity Provider',
    'E1': 'User interrupted',
    'E3': 'User failed to verify SSN',

    # Happens if an internal error happens at our side
    'E500': 'Internal Server Error',

    # Directly translated from Identity Provider's error code.
    # Happens if an internal error occurs at their side.
    'E501': 'Internal Server Error at Identity Provider',

    # Generic error (fallback error code).
    # Happens if we could not recognize error from Identity Provider.
    'E502': 'Internal Server Error at Identity Provider',

    # Happens if, for instance, we Identity Provider is offline,
    # and we could not fetch a token etc.
    'E505': 'Failed to communicate with Identity Provider',
}

# /callback?error_code=E501&error=Internal Serviver
