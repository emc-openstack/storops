# coding=utf-8
from __future__ import unicode_literals

from storops.lib.common import Enum, EnumList

__author__ = 'Cedric Zhuang'


class UnityEnum(Enum):
    @property
    def description(self):
        return self.value[1]

    @property
    def index(self):
        return self.value[0]

    @classmethod
    def indices(cls):
        return [i.index for i in cls.get_all()]

    def is_equal(self, value):
        return self.index == value

    def _get_properties(self, dec=0):
        if dec < 0:
            props = {'name': self.name}
        else:
            props = {'name': self.name,
                     'description': self.description,
                     'value': self.index}
        return props

    @classmethod
    def from_int(cls, value):
        for item in cls.get_all():
            if isinstance(item, UnityEnum):
                if item.value == value:
                    ret = item
                    break
        else:
            ret = super(UnityEnum, cls).from_int(value)
        return ret


class UnityEnumList(EnumList):
    @classmethod
    def get_enum_class(cls):
        raise NotImplementedError('enum class of this list is not defined.')


class HealthEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    OK = (5, 'OK')
    OK_BUT = (7, 'OK But Minor Warning')
    DEGRADED = (10, 'Degraded')
    MINOR = (15, 'Minor Issue')
    MAJOR = (20, 'Major Issue')
    CRITICAL = (25, 'Critical Issue')
    NON_RECOVERABLE = (30, 'Non Recoverable Issue')


class StorageResourceTypeEnum(UnityEnum):
    FILE_SYSTEM = (1, 'File System')
    CONSISTENCY_GROUP = (2, 'Consistency Group')
    VMWARE_FS = (3, 'VMware FS')
    VMWARE_ISCSI = (4, 'VMware iSCSI')
    LUN = (8, 'LUN')
    VVOL_DATASTORE_FS = (9, 'VVol DataStore FS')
    VVOL_DATASTORE_ISCSI = (10, 'VVol DataStore iSCSI')


class RaidTypeEnum(UnityEnum):
    NONE = (0, 'None')
    RAID5 = (1, 'RAID 5')
    RAID0 = (2, 'RAID 0')
    RAID1 = (3, 'RAID 1')
    RAID3 = (4, 'RAID 3')
    RAID10 = (7, 'RAID 10')
    RAID6 = (10, 'RAID 6')
    MIXED = (12, 'Mixed')
    AUTOMATIC = (48879, 'Automatic')


class RaidTypeEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return RaidTypeEnum


class ReplicationTypeEnum(UnityEnum):
    NONE = (0, 'No Replication')
    LOCAL = (1, 'Local Replication')
    REMOTE = (2, 'Remote Replication')


class NasServerUnixDirectoryServiceEnum(UnityEnum):
    NONE = (0, 'No Directory Service')
    NIS = (2, 'Use NIS Server')
    LDAP = (3, 'Use LDAP Server')


class FilesystemTypeEnum(UnityEnum):
    FILESYSTEM = (1, 'File System')
    VMWARE = (2, 'VMware')


class TieringPolicyEnum(UnityEnum):
    AUTOTIER_HIGH = (0, 'Start Highest and Auto-tier')
    AUTOTIER = (1, 'Auto-tier')
    HIGHEST = (2, 'Highest')
    LOWEST = (3, 'Lowest')
    NO_DATA_MOVEMENT = (4, 'No Data Movement')
    MIXED = (0xffff, 'Different Tier Policies')


class TieringPolicyEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return TieringPolicyEnum


class FSSupportedProtocolEnum(UnityEnum):
    NFS = (0, 'NFS')
    CIFS = (1, 'CIFS')
    MULTI_PROTOCOL = (2, 'Multiprotocol')


class AccessPolicyEnum(UnityEnum):
    NATIVE = (0, 'Native')
    UNIX = (1, 'Unix')
    WINDOWS = (2, 'Windows')


class FSFormatEnum(UnityEnum):
    UFS32 = (0, 'UFS32')
    UFS64 = (2, 'UFS64')


class HostIOSizeEnum(UnityEnum):
    GENERAL_8K = (0x2000, '8K for General Purpose')
    GENERAL_16K = (0x4000, '16K for General Purpose')
    GENERAL_32K = (0x8000, '32K for General Purpose')
    GENERAL_64K = (0x10000, '64K for General Purpose')
    EXCHANGE_2007 = (0x2001, '8K for Exchange 2007')
    EXCHANGE_2010 = (0x8001, '32K for Exchange 2010')
    EXCHANGE_2013 = (0x8002, '32K for Exchange 2013')
    ORACLE = (0x2002, '8K for Oracle DB')
    SQL_SERVER = (0x2003, '8K for MS SQL Server')
    VMWARE_HORIZON = (0x2004, '8K for VMware Horizon VDI')
    SHARE_POINT = (0x8003, '32K for SharePoint')
    SAP = (0x2005, '8K for SAP')


class ResourcePoolFullPolicyEnum(UnityEnum):
    DELETE_ALL_SNAPS = (0, 'Delete All Snaps')
    FAIL_WRITES = (1, 'Fail Writes')


class CIFSTypeEnum(UnityEnum):
    CIFS_SHARE = (1, 'Share on a File System')
    CIFS_SNAPSHOT = (2, 'Share on a Snapshot')


class CifsShareOfflineAvailabilityEnum(UnityEnum):
    MANUAL = (0, 'Manual')
    DOCUMENTS = (1, 'Documents')
    PROGRAMS = (2, 'Programs')
    NONE = (3, 'None')
    INVALID = (255, 'Invalid')


class NFSTypeEnum(UnityEnum):
    NFS_SHARE = (1, 'Share on a File System')
    VMWARE_NFS = (2, 'Share on a VMware Data Store')
    NFS_SNAPSHOT = (3, 'Share on a Snapshot')


class NFSShareRoleEnum(UnityEnum):
    PRODUCTION = (0, "for Production")
    BACKUP = (1, "for Backup")


class NFSShareDefaultAccessEnum(UnityEnum):
    NO_ACCESS = (0, "No Access")
    READ_ONLY = (1, "Read Only")
    READ_WRITE = (2, "Read Write")
    ROOT = (3, "Root")


class NFSShareSecurityEnum(UnityEnum):
    SYS = (0, 'any NFS security types')
    KERBEROS = (1, 'Kerberos')
    KERBEROS_WITH_INTEGRITY = (2, 'Kerberos with integrity')
    KERBEROS_WITH_ENCRYPTION = (3, 'Kerberos with Encryption Security')


class SnapCreatorTypeEnum(UnityEnum):
    NONE = (0, 'Not Specified')
    SCHEDULED = (1, 'Created by Schedule')
    USER_CUSTOM = (2, 'Created by User with a Custom Name')
    USER_DEFAULT = (3, 'Created by User with a Default Name')
    EXTERNAL_VSS = (4, 'Created by VSS')
    EXTERNAL_NDMP = (5, 'Created by NDMP')
    EXTERNAL_RESTORE = (6, 'Created as a Backup before a Restore')
    EXTERNAL_REPLICATION_MANAGER = (8, 'Created by Replication Manger')
    REP_V2 = (9, 'Created by Native Replication')
    INBAND = (11, 'Created by SnapCLI')


class SnapStateEnum(UnityEnum):
    READY = (2, 'Ready')
    FAULTED = (3, 'Faulted')
    OFFLINE = (6, 'Offline')
    INVALID = (7, 'Invalid')
    INITIALIZING = (8, 'Initializing')
    DESTROYING = (9, 'Destroying')


class SnapAccessLevelEnum(UnityEnum):
    READ_ONLY = (0, 'Read Only')
    READ_WRITE = (1, 'Read Write')


class FilesystemSnapAccessTypeEnum(UnityEnum):
    CHECKPOINT = (1, 'Checkpoint')
    PROTOCOL = (2, 'Protocol')


class RaidStripeWidthEnum(UnityEnum):
    BEST_FIT = (0, '')
    _2 = (2, '2 disk group, usable in RAID10')
    _4 = (4, '4 disk group, usable in RAID10')
    _5 = (5, '5 disk group, usable in RAID5')
    _6 = (6, '6 disk group, usable in RAID6 and RAID10')
    _8 = (8, '8 disk group, usable in RAID6 and RAID10')
    _9 = (9, '9 disk group, usable in RAID5')
    _10 = (10, '10 disk group, usable in RAID6 and RAID10')
    _12 = (12, '12 disk group, usable in RAID6 and RAID10')
    _13 = (13, '13 disk group, usable in RAID5')
    _14 = (14, '14 disk group, usable in RAID6')
    _16 = (16, 'including parity disks, usable in RAID6')


class FastVPStatusEnum(UnityEnum):
    NOT_APPLICABLE = (1, 'Not applicable')
    PAUSED = (2, 'Paused')
    ACTIVE = (3, 'Active')
    NOT_STARTED = (4, 'Not Started')
    COMPLETED = (5, 'Completed')
    STOPPED_BY_USER = (6, 'Stopped by User')
    FAILED = (7, 'Failed')


class FastVPRelocationRateEnum(UnityEnum):
    HIGH = (1, 'High')
    MEDIUM = (2, 'Medium')
    LOW = (3, 'Low')
    NONE = (4, 'None')


class PoolDataRelocationTypeEnum(UnityEnum):
    MANUAL = (1, 'Manual')
    SCHEDULED = (2, 'Scheduled')
    REBALANCE = (3, 'Rebalance')


class UsageHarvestStateEnum(UnityEnum):
    IDLE = (0, 'Idle')
    RUNNING = (1, 'Running')
    COULD_NOT_REACH_LWM = (2, 'Could not Reach LWM')
    PAUSED_COULD_NOT_REACH_HWM = (3, 'Paused Could not Reach LWM')
    FAILED = (4, 'Failed')


class TierTypeEnum(UnityEnum):
    NONE = (0, 'None')
    EXTREME_PERFORMANCE = (10, 'Extreme Performance')
    PERFORMANCE = (20, 'Performance')
    CAPACITY = (30, 'Capacity')


class PoolUnitTypeEnum(UnityEnum):
    RAID_GROUP = (1, 'RAID Group')
    VIRTUAL_DISK = (2, 'Virtual Disk')


class IpProtocolVersionEnum(UnityEnum):
    IPv4 = (4, 'IPv4')
    IPv6 = (6, 'IPv6')


class FileInterfaceRoleEnum(UnityEnum):
    PRODUCTION = (0, 'Production')
    BACKUP = (1, 'Backup')


class ReplicationPolicyEnum(UnityEnum):
    NOT_REPLICATED = (0, 'Not Replicated')
    Replicated = (1, 'Replicated')
    OVERRIDDEN = (2, 'Overridden')


class EnclosureTypeEnum(UnityEnum):
    DERRINGER_6G_SAS_DAE = (20, '25 Drive 6G DAE')
    PINECONE_6G_SAS_DAE = (26, '12 Drive 6G DAE')
    STEELJAW_6G_SAS_DPE = (27, '12 Drive 6G DPE')
    RAMHORN_6G_SAS_DPE = (28, '25 Drive 6G DPE')
    TABASCO_12G_SAS_DAE = (29, '25 Drive 12G DAE')
    ANCHO_12G_SAS_DAE = (30, '15 Drive 12G DAE')
    MIRANDA_12G_SAS_DPE = (36, '25 Drive 12G DPE')
    RHEA_12G_SAS_DPE = (37, '12 Drive 12G DPE')
    VIRTUAL_DPE = (100, 'Virtual DPE')
    UNSUPPORTED = (999, 'Unsupported Enclosure')


class DiskTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unsupported')
    SAS = (5, 'SAS')
    SAS_FLASH = (9, 'SAS Flash')
    NL_SAS = (10, 'Near-line SAS')
    SAS_FLASH_2 = (11, 'SAS Medium Endurance Flash')
    SAS_FLASH_3 = (12, 'SAS Low Endurance Flash')


class DiskTypeEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return DiskTypeEnum


class KdcTypeEnum(UnityEnum):
    CUSTOM = (0, 'Custom')
    UNIX = (1, 'Unix')
    WINDOWS = (2, 'Windows')


class ThinStatusEnum(UnityEnum):
    FALSE = (0, 'False')
    TRUE = (1, 'True')
    MIXED = (0xffff, 'Mixed')


class DedupStatusEnum(UnityEnum):
    DISABLED = (0, 'Disabled')
    ENABLED = (1, 'Enabled')
    MIXED = (0xffff, 'Mixed')


class ESXFilesystemMajorVersionEnum(UnityEnum):
    VMFS_3 = (3, 'VMFS 3')
    VMFS_5 = (5, 'VMFS 5')


class ESXFilesystemBlockSizeEnum(UnityEnum):
    _1MB = (1, '1 MB')
    _2MB = (2, '2 MB')
    _4MB = (4, '4 MB')
    _8MB = (8, '8 MB')


class ScheduleVersionEnum(UnityEnum):
    LEGACY = (1, 'Legacy Schedule')
    SIMPLE = (2, 'Simple Schedule')


class ScheduleTypeEnum(UnityEnum):
    N_HOURS_AT_MM = (0, 'Every N hours, at MM')
    DAY_AT_HHMM = (1, 'Each day at HH:MM')
    N_DAYS_AT_HHMM = (2, 'Every N days at HH:MM')
    SELDAYS_AT_HHMM = (3, 'On SEL days of week at HH:MM')
    NTH_DAYOFMONTH_AT_HHMM = (4, 'On Nth day of month at HH:MM')
    UNSUPPORTED = (5, 'Not supported')


class HostLUNAccessEnum(UnityEnum):
    NO_ACCESS = (0, 'No Access')
    PRODUCTION = (1, 'Production LUNs only')
    SNAPSHOT = (2, 'LUN Snapshots only')
    BOTH = (3, 'Production LUNs and Snapshots')
    MIXED = (0xffff, 'Mixed')


class HostTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    HOST_MANUAL = (1, 'Manual Defined Host')
    SUBNET = (2, 'Hosts in a Subnet')
    NET_GROUP = (3, 'Net Group')
    RPA = (4, 'RecoverPoint Appliance')
    HOST_AUTO = (5, 'Auto-managed Host')


class HostManageEnum(UnityEnum):
    UNKNOWN = (0, "Manged Manually")
    VMWARE = (1, 'Auto-managed by ESX Server')
    OTHERS = (2, 'Other Methods')


class HostRegistrationTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Registration Type Unknown')
    MANUAL = (1, 'Manually Registered Initiator')
    ESX_AUTO = (2, 'ESX Auto-registered Initiator')


class HostContainerTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    ESX = (1, 'ESX')
    VCENTER = (2, 'vCenter')


class HostInitiatorTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    FC = (1, 'FC')
    ISCSI = (2, 'iSCSI')


class HostInitiatorPathTypeEnum(UnityEnum):
    MANUAL = (0, 'Manual')
    ESX_AUTO = (1, 'ESX Auto')
    OTHER_AUTO = (2, 'Other Auto')


class HostInitiatorIscsiTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    HARDWARE = (1, 'Hardware')
    SOFTWARE = (2, 'Software')
    DEPENDENT = (3, 'Dependent')


class HostInitiatorSourceTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    HP_AUTO_TRESPASS = (2, 'HP with Auto-Trespass')
    OPEN_NATIVE = (3, 'Open Native')
    SGI = (9, 'Silicon Graphics')
    HP_NO_AUTO_TRESPASS = (10, 'HP without Auto-Traspass')
    DELL = (19, 'Dell')
    FUJITSU_SIEMENS = (22, 'Fujitsu-Siemens')
    CLARIION_ARRAY_CMI = (25, 'Remote CLARiiON array')
    TRU64 = (28, 'Tru64')
    RECOVER_POINT = (31, 'RecoverPoint')


class DatastoreTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    VMFS_3 = (1, 'VMFS 3')
    VMFS_5 = (2, 'VMFS 5')


class VMDiskTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    VMFS_THICK = (1, 'VMFS Thick')
    VMFS_THIN = (2, 'VMFS Thin')
    RDM_PHYSICAL = (3, 'RDM Physical')
    RDM_VIRTUAL = (4, 'RDM Virtual')


class VMPowerStateEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    OFF = (1, 'Off')
    ON = (2, 'On')
    SUSPENDED = (3, 'Suspended')
    PAUSED = (4, 'Paused')


class VVolTypeEnum(UnityEnum):
    CONFIG = (0, 'Config')
    DATA = (1, 'Data')
    SWAP = (2, 'Swap')
    MEMORY = (3, 'Memory')
    OTHER = (99, 'Other')


class ReplicaTypeEnum(UnityEnum):
    BASE = (0, 'Base vVol')
    PRE_SNAPSHOT = (1, 'Prepared Snapshot vVol')
    SNAPSHOT = (2, 'Snapshot vVol')
    FAST_CLONE = (3, 'Fast-clone vVol')


class HostPortTypeEnum(UnityEnum):
    IPv4 = (0, 'IPv4')
    IPv6 = (1, 'IPv6')
    NETWORK_NAME = (2, 'Network Name')


class HostLUNTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    LUN = (1, 'Production LUN')
    LUN_SNAP = (2, 'Snapshot LUN')


class FcSpeedEnum(UnityEnum):
    AUTO = (0, 'Auto')
    _1GbPS = (1, '1GbPS')
    _2GbPS = (2, '2GbPS')
    _4GbPS = (4, '4GbPS')
    _8GbPS = (8, '8GbPS')
    _16GbPS = (16, '16GbPS')
    _32GbPS = (32, '32GbPS')


class FcSpeedEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return FcSpeedEnum


class SFPSpeedValuesEnum(UnityEnum):
    AUTO = (0, 'Auto')
    _10MbPS = (10, '10MbPS')
    _100MbPS = (10, '100MbPS')
    _1GbPS = (1000, '1GbPS')
    _1500MbPS = (1500, '1500MbPS')
    _2GbPS = (2000, '2GbPS')
    _3GbPS = (3000, '3GbPS')
    _4GbPS = (4000, '4GbPS')
    _6GbPS = (6000, '6GbPS')
    _8GbPS = (8000, '8GbPS')
    _10GbPS = (10000, '10GbPS')
    _12GbPS = (12000, '12GbPS')
    _16GbPS = (16000, '16GbPS')
    _32GbPS = (32000, '32GbPS')
    _40GbPS = (40000, '40GbPS')
    _100GbPS = (100000, '100GbPS')
    _1TbPS = (1000000, '1TbPS')


class SFPSpeedValuesEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return SFPSpeedValuesEnum


class SFPProtocolValuesEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    FC = (1, 'FC')
    ETHERNET = (2, 'Ethernet')
    SAS = (3, 'SAS')


class SFPProtocolValuesEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return SFPProtocolValuesEnum


class ConnectorTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    RJ45 = (1, 'RJ45')
    LC = (2, 'LC')
    MINI_SAS_HD = (3, 'MiniSAS HD')
    COPPER_PIGTAIL = (4, "Copper pigtail")
    NO_SEPARABLE_CONNECTOR = (5, "No separable connector")
    NAS_COPPER = (6, "NAS copper")
    NOT_PRESENT = (7, "Not present")


class EPSpeedValuesEnum(UnityEnum):
    AUTO = (0, 'Auto')
    _10MbPS = (10, '10MbPS')
    _100MbPS = (100, '100MbPS')
    _1GbPS = (1000, '1GbPS')
    _10GbPS = (10000, '10GbPS')
    _40GbPS = (40000, '40GbPS')
    _100GbPS = (100000, '100GbPS')
    _1TbPS = (1000000, '1TbPS')


class EPSpeedValuesEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return EPSpeedValuesEnum


class DiskTierEnum(UnityEnum):
    EXTREME_PERFORMANCE = (0, 'Extreme Performance')
    PERFORMANCE = (1, 'Performance')
    CAPACITY = (2, 'Capacity')
    EXTREME_MULTI = (3, 'Multi-tier with Flash')
    MULTI = (4, 'Multi-tier without Flash')


class DiskTierEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return DiskTierEnum


class FastCacheStateEnum(UnityEnum):
    OFF = (0, 'Off')
    ON = (1, 'On')


class FastCacheStateEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return FastCacheStateEnum


class SpaceEfficiencyEnum(UnityEnum):
    THICK = (0, 'Thick')
    THIN = (1, 'Thin')


class SpaceEfficiencyEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return SpaceEfficiencyEnum


class ServiceLevelEnum(UnityEnum):
    BASIC = (0, 'Basic')
    BRONZE = (1, 'Bronze')
    SILVER = (2, 'Silver')
    GOLD = (3, 'Gold')
    PLATINUM = (4, 'PLATINUM')


class ServiceLevelEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return ServiceLevelEnum


class VmwarePETypeEnum(UnityEnum):
    NAS = (0, 'NAS')
    SCSI = (1, 'SCSI')


class NodeEnum(UnityEnum):
    SPA = (0, 'SPA')
    SPB = (1, 'SPB')
    UNKNOWN = (2989, 'Unknown')


class LUNTypeEnum(UnityEnum):
    GENERIC = (1, 'Generic Storage')
    STANDALONE = (2, 'Standalone Storage')
    VMWARE_ISCSI = (3, 'VMware Storage')


class JobStateEnum(UnityEnum):
    QUEUED = (1, 'Queued')
    RUNNING = (2, 'Running')
    SUSPENDED = (3, 'Suspended')
    COMPLETED = (4, 'Completed')
    FAILED = (5, 'Failed')
    ROLLING_BACK = (6, 'Rolling Back')
    COMPLETED_WITH_ERROR = (7, 'Completed with Error')


class JobTaskStateEnum(UnityEnum):
    NOT_STARTED = (0, 'Not Started')
    RUNNING = (1, 'Running')
    COMPLETED = (2, 'Completed')
    FAILED = (3, 'Failed')
    ROLLING_BACK = (5, 'Rolling Back')


class SeverityEnum(UnityEnum):
    OK = (8, 'OK')
    DEBUG = (7, 'Debug')
    INFO = (6, 'Info')
    NOTICE = (5, 'Notice')
    WARNING = (4, 'Warning')
    ERROR = (3, 'Error')
    CRITICAL = (2, 'Critical')
    ALERT = (1, 'Alert')
    EMERGENCY = (0, 'Emergency')


class ACEAccessTypeEnum(UnityEnum):
    DENY = (0, 'Deny')
    GRANT = (1, 'Grant')
    NONE = (2, 'None')


class ACEAccessLevelEnum(UnityEnum):
    READ = (1, 'Read')
    WRITE = (2, 'Write')
    FULL = (4, 'Full')


class IOLimitPolicyStateEnum(UnityEnum):
    GLOBAL_PAUSED = (1, 'Global Paused')
    PAUSED = (2, 'Paused')
    ACTIVE = (3, 'Active')


class IOLimitPolicyTypeEnum(UnityEnum):
    ABSOLUTE = (1, 'Absolute Value')
    DENSITY_BASED = (2, 'Density-based Value')


class DNSServerOriginEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    STATIC = (1, 'Set Manually')
    DHCP = (2, 'Configured by DHCP')


class MetricTypeEnum(UnityEnum):
    UNKNOWN = (1, 'Unknown')
    COUNTER_32 = (2, '32 bits Counter')
    COUNTER_64 = (3, '64 bits Counter')
    RATE = (4, 'Rate')
    FACT = (5, 'Fact')
    TEXT = (6, 'Text')
    VIRTUAL_COUNTER_32 = (7, '32 bits Virtual Counter')
    VIRTUAL_COUNTER_64 = (8, '64 bits Virtual Counter')


class DiskTechnologyEnum(UnityEnum):
    SAS = (1, 'SAS')
    NL_SAS = (2, 'NL_SAS')
    SAS_FLASH_2 = (6, 'SAS_FLASH_2')
    SAS_FLASH_3 = (7, 'SAS_FLASH_3')
    MIXED = (50, 'Mixed')
    VIRTUAL = (99, 'Virtual')
