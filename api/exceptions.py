class ArtDashExceptions(Exception):
    """Super class for all ART bot exceptions"""
    pass


# Art bot exceptions
class DistgitNotFound(ArtDashExceptions):
    """Exception raised for errors in the input dist-git name."""
    pass


class CdnFromBrewNotFound(ArtDashExceptions):
    """Exception raised if CDN is not found from brew name and variant"""
    pass


class CdnNotFound(ArtDashExceptions):
    """Exception raised if CDN is not found from CDN name"""
    pass


class DeliveryRepoNotFound(ArtDashExceptions):
    """Exception raised if delivery repo not found"""
    pass


class BrewIdNotFound(ArtDashExceptions):
    """Exception raised if brew id not found for the given brew package name"""
    pass


class VariantIdNotFound(ArtDashExceptions):
    """Exception raised if variant id not found for a CDN repo"""
    pass


class CdnIdNotFound(ArtDashExceptions):
    """Exception raised if CDN id not found for a CDN repo"""
    pass


class ProductIdNotFound(ArtDashExceptions):
    """Exception raised if Product id not found for a product variant"""
    pass


class DeliveryRepoUrlNotFound(ArtDashExceptions):
    """Exception raised if delivery repo not found on Pyxis."""
    pass


class DeliveryRepoIDNotFound(ArtDashExceptions):
    """Exception raised if delivery repo ID not found on Pyxis."""
    pass


class GithubFromDistgitNotFound(ArtDashExceptions):
    """Exception raised if GitHub repo could not be found from the distgit name"""
    pass


class DistgitFromGithubNotFound(ArtDashExceptions):
    """Exception raised if Distgit repo could not be found from the GitHub repo name"""
    pass


class MultipleCdnToBrewMappings(ArtDashExceptions):
    """Exception raised if more than one Brew packages are found for a CDN repo"""
    pass


class BrewNotFoundFromCdnApi(ArtDashExceptions):
    """Exception raised when the json file returned from the CDN repos API does not have Brew packages listed"""
    pass


class BrewFromDeliveryNotFound(ArtDashExceptions):
    """Exception raised when the brew name could not be retrieved from pyxis"""
    pass


class MultipleBrewFromDelivery(ArtDashExceptions):
    """Exception raised if more than one delivery to brew mappings found"""
    pass


class BrewToCdnWithDeliveryNotFound(ArtDashExceptions):
    """Exception raised when we cannot found the CDN repo name using the Brew name that we got using the Delivery Repo name"""
    pass


class DistgitFromBrewNotFound(ArtDashExceptions):
    """Exception raised when we cannot find the distgit name from the given brew name"""


class NullDataReturned(ArtDashExceptions):
    """Exception raise when null data (empty dict, list etc.) is returned from any function, which is necessary for other functions"""


class BrewToDistgitMappingNotFound(ArtDashExceptions):
    """Exception raised when no mapping is found between brew and distgit from the yml file from ocp-build-data/images"""


# Other exceptions
class InternalServicesExceptions(Exception):
    """Super class for all exceptions while trying to access internal services"""
    pass


class KojiClientError(InternalServicesExceptions):
    """Exception raised when we cannot connect to brew."""
    pass


class KerberosAuthenticationError(InternalServicesExceptions):
    """Exception raised for Authentication error if keytab or ticket is missing
    """


class AccessDenied(InternalServicesExceptions):
    """Exception raised for Authentication errors
    """
