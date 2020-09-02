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
    MIXED = (3, 'More than one async replication session involved resources '
                'on local system')


class NasServerUnixDirectoryServiceEnum(UnityEnum):
    NONE = (0, 'No Directory Service')
    LOCAL = (1, 'Use local files for looking up identity information.')
    NIS = (2, 'Use NIS Server')
    LDAP = (3, 'Use LDAP Server')
    LOCAL_THEN_NIS = (4, 'Local Then NIS')
    LOCAL_THEN_LDAP = (5, 'Local Then LDAP')


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
    RO_ROOT = (4, "Read Only Root")


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
    APP_SYNC = (12, 'Created by AppSync')


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
    READ_ONLY_PARTIAL = (2, 'Read Only Partial')
    READ_WRITE_PARTIAL = (3, 'Read Write Partial')
    MIXED = (4, 'Mixed')


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
    NVME_EXTREME_PERFORMANCE = (5, 'NVMe Extreme Performance')
    EXTREME_PERFORMANCE = (10, 'Extreme Performance')
    PERFORMANCE = (20, 'Performance')
    CAPACITY = (30, 'Capacity')


class PoolUnitTypeEnum(UnityEnum):
    RAID_GROUP = (1, 'RAID Group')
    VIRTUAL_DISK = (2, 'Virtual Disk')


class StoragePoolTypeEnum(UnityEnum):
    DYNAMIC = (1, 'Dynamic')
    TRADITIONAL = (2, 'Traditional')


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
    UNKNOWN_ENCLOSURE = (0, 'Unknown Enclosure')
    DERRINGER_6G_SAS_DAE = (20, '25 Drive 6G DAE')
    PINECONE_6G_SAS_DAE = (26, '12 Drive 6G DAE')
    STEELJAW_6G_SAS_DPE = (27, '12 Drive 6G DPE')
    RAMHORN_6G_SAS_DPE = (28, '25 Drive 6G DPE')
    TABASCO_12G_SAS_DAE = (29, '25 Drive 12G DAE')
    ANCHO_12G_SAS_DAE = (30, '15 Drive 12G DAE')
    NAGA_12G_SAS_DAE = (32, '80 Drive 12G DAE')
    MIRANDA_12G_SAS_DPE = (36, '25 Drive 12G DPE')
    RHEA_12G_SAS_DPE = (37, '12 Drive 12G DPE')
    SCORP_12G_SAS_DPE = (38, '25 Drive 12G DPE')
    VIRTUAL_DPE = (100, 'Virtual DPE')
    UNSUPPORTED = (999, 'Unsupported Enclosure')


class DiskTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unsupported')
    SAS = (5, 'SAS')
    SAS_FLASH = (9, 'SAS Flash')
    NL_SAS = (10, 'Near-line SAS')
    SAS_FLASH_2 = (11, 'SAS Medium Endurance Flash')
    SAS_FLASH_3 = (12, 'SAS Low Endurance Flash')
    SAS_FLASH_4 = (13, 'SAS Low Endurance Flash')
    NVME_FLASH = (16, 'The NVMe Flash drive can be used for the NVMe Extreme '
                      'Performance storage pool tier.')
    NVME_FLASH_1 = (18, 'The low Endurance NVMe Flash drive can be used for '
                        'the NVMe Extreme Performance storage pool tier but '
                        'not for the FAST Cache.')
    NVME_FLASH_2 = (19, 'The Read Intensive NVMe FLASH drive can only be used '
                        'for NVMe Extreme Performance storage pool but not '
                        'for the FAST Cache.')


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
    VMFS_6 = (6, 'VMFS 6')


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
    # Applies to consistency groups only
    MIXED = (0xffff, 'Mixed')


class HostTypeEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    HOST_MANUAL = (1, 'Manual Defined Host')
    SUBNET = (2, 'Hosts in a Subnet')
    NET_GROUP = (3, 'Net Group')
    RPA = (4, 'RecoverPoint Appliance')
    HOST_AUTO = (5, 'Auto-managed Host')
    VNX_SAN_COPY = (255, 'VNX Block Migration system')


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
    VMFS_6 = (3, 'VMFS 6')


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
    _25GbPS = (25000, '25GbPS')
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


class SpeedValuesEnum(UnityEnum):
    _3Gbps = (3, "3Gbps")
    _6Gbps = (6, "6Gbps")
    _12Gbps = (12, "12Gbps")


class EPSpeedValuesEnum(UnityEnum):
    AUTO = (0, 'Auto')
    _10MbPS = (10, '10MbPS')
    _100MbPS = (100, '100MbPS')
    _1GbPS = (1000, '1GbPS')
    _10GbPS = (10000, '10GbPS')
    _25GbPS = (25000, '25GbPS')
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
    NVME_EXTREME_PERFORMANCE_TIER = (5, 'Tier that maps to NVMe drives.')
    NVME_EXTREME_MULTI_TIER = (6, 'Multi-tiered pool that includes NVMe tier.')


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
    COMPLETED_WITH_PROBLEMS = (6, 'Completed With Errors')
    SUSPENDED = (7, 'Suspended')


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
    EFD = (5, 'EFD')
    SAS_FLASH_2 = (6, 'SAS_FLASH_2')
    SAS_FLASH_3 = (7, 'SAS_FLASH_3')
    SAS_FLASH_4 = (8, 'SAS_FLASH_4')
    SAS_FLASH_5 = (9, 'SAS_FLASH_5')
    NVME_FLASH_1 = (10, 'The Low Endurance NVMe Flash drive can be used for '
                        'the NVMe Extreme Performance storage pool tier but '
                        'not for the FAST Cache.')
    NVME_FLASH_2 = (11, 'The Read Intensive NVMe Flash drive can only be used '
                        'for the NVMe Extreme Performance Pool and cannot be '
                        'used for FAST Cache.')
    MIXED = (50, 'Mixed')
    VIRTUAL = (99, 'Virtual')


class ThinCloneActionEnum(UnityEnum):
    DD_COPY = (1, 'Copy via dd')
    LUN_ATTACH = (2, 'Attach a base LUN')
    TC_DELETE = (3, 'Delete a thin-cloned LUN')
    BASE_LUN_DELETE = (4, 'Delete the base LUN of a thin-cloned LUN')


class FeatureStateEnum(UnityEnum):
    Disabled = (1, "FeatureStateDisabled")
    Enabled = (2, "FeatureStateEnabled")
    Hidden = (3, "FeatureStateHidden")


class FeatureReasonEnum(UnityEnum):
    UNLICENSED = (1, "FeatureReasonUnlicensed")
    EXPIRED_LICENSE = (2, "FeatureReasonExpiredLicense")
    PLATFORM_RESTRICTION = (3, "FeatureReasonPlatformRestriction")
    EXCLUDED = (4, "FeatureReasonExcluded")


class HotSparePolicyStatusEnum(UnityEnum):
    OK = (0, "OK")
    VIOLATED = (741, "Violated")


class InterfaceConfigModeEnum(UnityEnum):
    DISABLED = (0, "Disabled")
    STATIC = (1, "Static")
    AUTO = (2, "Auto")


class MoveSessionStateEnum(UnityEnum):
    INITIALIZING = (0, "Initializing")
    QUEUED = (1, "Queued")
    RUNNING = (2, "Running")
    FAILED = (3, "Failed")
    CANCELLING = (4, "Cancelling")
    CANCELLED = (5, "Cancelled")
    COMPLETED = (6, "Completed")


class MoveSessionStatusEnum(UnityEnum):
    INITIALIZING = (0, "OK")
    POOL_OFFLINE = (1, "PoolOffline")
    POOL_OUT_OF_SPACE = (2, "PoolOutOfSpace")
    INTERNAL_ERROR = (3, "InternalError")


class MoveSessionPriorityEnum(UnityEnum):
    IDLE = (0, "Idle")
    LOW = (1, "Low")
    BELOW_NORMAL = (2, "Below_Normal")
    NORMAL = (3, "Normal")
    ABOVE_NORMAL = (4, "Above_Normal")
    HIGH = (5, "High")


class ReplicationSessionStatusEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    OTHER = (1, 'Other')
    OK = (2, 'OK')
    PAUSED = (3, 'Paused')
    FATAL_REPLICATION_ISSUE = (4, 'Fatal_Replication_Issue')
    LOST_COMMUNICATION = (5, 'Lost_Communication')
    FAILED_OVER = (6, 'Failed_Over')
    FAILED_OVER_WITH_SYNC = (7, 'Failed_Over_With_Sync')
    DESTINATION_EXTEND_NOT_SYNCING = (8, 'Destination_Extend_Not_Syncing')
    DESTINATION_EXTEND_IN_PROGRESS = (9, 'Destination_Extend_In_Progress')
    LOST_SYNC_COMMUNICATION = (10, 'Lost_Sync_Communication')
    DESTINATION_POOL_OUT_OF_SPACE = (11, 'Destination_Pool_Out_Of_Space')


class ReplicationSessionNetworkStatusEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    OTHER = (1, 'Other')
    OK = (2, 'OK')
    LOST_COMMUNICATION = (5, 'Lost_Communication')
    LOST_SYNC_COMMUNICATION = (10, 'Lost_Sync_Communication')
    ZERO_BANDWIDTH_CONFIGURED = (18, 'Data transfer is suspended because '
                                     'bandwidth is set to 0')


class ReplicationSessionSyncStateEnum(UnityEnum):
    MANUAL_SYNCING = (0, 'Manual_Syncing')
    AUTO_SYNCING = (1, 'Auto_Syncing')
    IDLE = (2, 'Idle')
    UNKNOWN = (100, 'Unknown')
    OUT_OF_SYNC = (101, 'Out_Of_Sync')
    IN_SYNC = (102, 'In_Sync')
    CONSISTENT = (103, 'Consistent')
    SYNCING = (104, 'Syncing')
    INCONSISTENT = (105, 'Inconsistent')


class ReplicationSessionReplicationRoleEnum(UnityEnum):
    SOURCE = (0, 'Source')
    DESTINATION = (1, 'Destination')
    LOOPBACK = (2, 'Loopback')
    LOCAL = (3, 'Local')
    UNKNOWN = (4, 'Unknown')


class ReplicationCapabilityEnum(UnityEnum):
    SYNC = (0, 'Sync')
    ASYNC = (1, 'Async')
    BOTH = (2, 'Both')
    NONE = (3, 'None')


class ReplicationEndpointResourceTypeEnum(UnityEnum):
    FILESYSTEM = (1, 'filesystem')
    CONSISTENCYGROUP = (2, 'consistencyGroup')
    VMWAREFS = (3, 'vmwarefs')
    VMWAREISCSI = (4, 'vmwareiscsi')
    LUN = (8, 'lun')
    NASSERVER = (10, 'nasServer')


class ReplicationOpStatusEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    OTHER = (1, 'Other')
    OK = (2, 'OK')
    NON_RECOVERABLE_ERROR = (7, 'Non_Recoverable_Error')
    LOST_COMMUNICATION = (13, 'Lost_Communication')
    FAILED_OVER_WITH_SYNC = (0x8400, 'Failed_Over_with_Sync')
    FAILED_OVER = (0x8401, 'Failed_Over')
    MANUAL_SYNCING = (0x8402, 'Manual_Syncing')
    PAUSED = (0x8403, 'Paused')
    IDLE = (0x8404, 'Idle')
    AUTO_SYNC_CONFIGURED = (0x8405, 'Auto_Sync_Configured')
    DESTINATION_EXTEND_FAILED_NOT_SYNCING = (
        0x840B, 'Destination_Extend_Failed_Not_Syncing')
    DESTINATION_EXTEND_IN_PROGRESS = (0x840C, 'Destination_Extend_In_Progress')
    ACTIVE = (0x840D, 'Active')
    LOST_SYNC_COMMUNICATION = (0x840E, 'Lost_Sync_Communication')
    DESTINATION_POOL_OUT_OF_SPACE = (0x840F, 'Destination_Pool_Out_Of_Space')
    SYNCING = (0x8411, 'Syncing')
    FAILED_OVER_WITH_SYNC_MIXED = (0x87E8, 'Failed_Over_with_Sync_Mixed')
    FAILED_OVER_MIXED = (0x87E9, 'Failed_Over_Mixed')
    MANUAL_SYNCING_MIXED = (0x87EA, 'Manual_Syncing_Mixed')
    PAUSED_MIXED = (0x87EB, 'Paused_Mixed')
    IDLE_MIXED = (0x87EC, 'Idle_Mixed')
    AUTO_SYNC_CONFIGURED_MIXED = (0x87ED, 'Auto_Sync_Configured_Mixed')
    HIBERNATED = (0x87EE, 'Source or destination is in hibernated state.')
    ZERO_BANDWIDTH_CONFIGURED = (0x87EF, 'Data transfer suspended due to zero '
                                         'bandwidth configured.')
    SOURCE_VDM_PERFORMANCE_DEGRADED = (0x87F0, 'Performance of source VDM is '
                                               'degraded.')


class SNMPAuthProtocolEnum(UnityEnum):
    NONE = (0, 'None')
    MD5 = (1, 'MD5')
    SHA = (2, 'SHA')


class SNMPPrivacyProtocolEnum(UnityEnum):
    NONE = (0, 'None')
    AES = (1, 'AES')
    DES = (2, 'DES')


class SNMPVersionEnum(UnityEnum):
    V1 = (1, 'v1')
    V2C = (2, 'v2c')
    V3 = (3, 'v3')


class RemoteObjectTypeEnum(UnityEnum):
    LUN = (0, 'lun')
    FILESYSTEM = (1, 'filesystem')
    CONSISTENCYGROUP = (2, 'consistencyGroup')
    NASSERVER = (3, 'nasServer')


class ImportUnixDirectoryServiceEnum(UnityEnum):
    LOCAL = (0, 'Local')
    NIS = (1, 'NIS')
    LDAP = (2, 'LDAP')
    LOCALTHENNIS = (3, 'LocalThenNis')
    LOCALTHENLDAP = (4, 'LocalThenLdap')
    NONE = (5, 'None')
    DIRECTMATCH = (6, 'DirectMatch')


class ImportUnixDirectoryServiceEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return ImportUnixDirectoryServiceEnum


class ImportCapabilityEnum(UnityEnum):
    IMPORTABLE = (0, 'Importable')
    NON_IMPORTABLE_INTERNAL_ERROR = (1, 'Non_importable_internal_error')
    NON_IMPORTABLE_ONLY_SUPPORT_VNX = (2, 'Non_importable_only_support_vnx')
    NON_IMPORTABLE_SRC_VDM_NAME_IN_USE_SESS_COMPLETED = (
        3, 'Non_importable_src_vdm_name_in_use_sess_completed')
    NON_IMPORTABLE_SRC_VDM_NAME_IN_USE_SESS_ACTIVE = (
        4, 'Non_importable_src_vdm_name_in_use_sess_active')
    NON_IMPORTABLE_SRC_VDM_NAME_IN_USE = (
        5, 'Non_importable_src_vdm_name_in_use')
    NON_IMPORTABLE_NO_UP_SRC_CLNT_IF = (6, 'Non_importable_no_up_src_clnt_if')
    NON_IMPORTABLE_NO_FS_ON_SRC_VDM = (7, 'Non_importable_no_fs_on_src_vdm')
    NON_IMPORTABLE_REACH_SRC_FS_LIMIT = (
        8, 'Non_importable_reach_src_fs_limit')
    NON_IMPORTABLE_NFSV4_NOT_SUPPORT = (9, 'Non_importable_nfsv4_not_support')
    NON_IMPORTABLE_SECNFS_NOT_SUPPORT = (
        10, 'Non_importable_secnfs_not_support')
    NON_IMPORTABLE_VDM_CANNOT_HAVE_CIFS_SERVER = (
        11, 'Non_importable_vdm_cannot_have_cifs_server')
    NON_IMPORTABLE_SRCMIGIF_MORE_ERROR = (
        12, 'Non_importable_srcmigif_more_error')
    NON_IMPORTABLE_SRCMIGIF_ERROR = (13, 'Non_importable_srcmigif_error')
    NON_IMPORTABLE_INVALID_VDM = (14, 'Non_importable_invalid_vdm')
    NON_IMPORTABLE_REACH_SRC_IF_LIMIT = (
        15, 'Non_importable_reach_src_if_limit')
    NON_IMPORTABLE_SRC_CS_NOT_PRIMARY = (
        16, 'Non_importable_src_cs_not_primary')


class VDMSupportedProtocolsEnum(UnityEnum):
    NFS = (0, 'NFS')
    CIFS = (1, 'CIFS')
    MULTIPROTOCOL = (2, 'Multiprotocol')
    CIFSANDNFS = (3, 'CIFSAndNFS')


class ImportStateEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    INITIALIZED = (50000, 'Initialized')
    INITIAL_COPY = (50001, 'Initial_Copy')
    READY_TO_CUTOVER = (50002, 'Ready_to_Cutover')
    PAUSED = (50003, 'Paused')
    CUTTING_OVER = (50004, 'Cutting_Over')
    INCREMENTAL_COPY = (50005, 'Incremental_Copy')
    READY_TO_COMMIT = (50006, 'Ready_to_Commit')
    COMMITTING = (50007, 'Committing')
    COMPLETED = (50008, 'Completed')
    CANCELLING = (50009, 'Cancelling')
    CANCELLED = (50010, 'Cancelled')
    PENDING = (50011, 'Pending')
    SYNCING = (50012, 'Syncing')
    ERROR = (50013, 'Error')


class ImportOpStatusEnum(UnityEnum):
    UNKNOWN = (0, 'Unknown')
    NON_RECOVERABLE_ERROR = (7, 'Non_Recoverable_Error')
    CONFIGURING_TARGET_RESOURCE = (32768, 'Configuring_Target_Resource')
    ENABLING_TARGET_RESOURCE_ACCESS = (
        32769, 'Enabling_Target_Resource_Access')
    MIGRATOR_CANNOT_DISCOVER_TARGET_RESOURCE = (
        32770, 'Migrator_Cannot_Discover_Target_Resource')
    READY_TO_MIGRATE = (32771, 'Ready_To_Migrate')
    INITIAL_TRANSFER_INPROGRESS = (32772, 'Initial_Transfer_Inprogress')
    DELTA_TRANSFER_INPROGRESS = (32773, 'Delta_Transfer_Inprogress')
    PAUSED = (32774, 'Paused')
    READY_TO_CUTOVER = (32776, 'Ready_To_Cutover')
    LOST_COMMUNICATION = (32777, 'Lost_Communication')
    TARGET_LUNS_OFFLINE = (32779, 'Target_Luns_Offline')
    PENDING = (32780, 'Pending')
    CUTOVER_SYNC_COMPLETE = (32781, 'Cutover_Sync_Complete')
    SESSION_CLEANUP_COMPLETE = (32782, 'Session_Cleanup_Complete')
    FINAL_TRANSFER_INPROGRESS = (32783, 'Final_Transfer_Inprogress')
    INITIALIZED = (33024, 'Initialized')
    STARTING = (33025, 'Starting')
    START_FAILED = (33026, 'Start_Failed')
    MIGRATING_DATA = (33027, 'Migrating_Data')
    MIGRATING_DATA_STOPPED = (33028, 'Migrating_Data_Stopped')
    MIGRATING_DATA_FAILED = (33029, 'Migrating_Data_Failed')
    MIGRATING_DATA_FAILED_STOPPED = (33030, 'Migrating_Data_Failed_Stopped')
    MIGRATING_CONFIGURATION = (33031, 'Migrating_Configuration')
    MIGRATING_CONFIGURATION_FAILED = (33032, 'Migrating_Configuration_Failed')
    MIGRATING_CONFIGURATION_PAUSED = (33033, 'Migrating_Configuration_Paused')
    CUTTING_OVER = (33280, 'Cutting_Over')
    CUTOVER_FAILED = (33281, 'Cutover_Failed')
    SYNCING_DATA = (33282, 'Syncing_Data')
    SYNCING_DATA_STOPPED = (33283, 'Syncing_Data_Stopped')
    SYNCING_DATA_FAILED = (33284, 'Syncing_Data_Failed')
    SYNCING_DATA_FAILED_STOPPED = (33285, 'Syncing_Data_Failed_Stopped')
    SESSION_EXCEED_LIMIT = (33532, 'Session_Exceed_Limit')
    READY_TO_COMPLETE = (33536, 'Ready_To_Complete')
    COMPLETING = (33537, 'Completing')
    COMPLETE_FAILED = (33538, 'Complete_Failed')
    COMPLETED = (33539, 'Completed')
    CANCELLING = (33540, 'Cancelling')
    CANCEL_FAILED = (33541, 'Cancel_Failed')
    CANCELLED = (33542, 'Cancelled')
    MIGRATING_DATA_STOPPING = (33543, 'Migrating_Data_Stopping')
    SYNCING_DATA_STOPPING = (33544, 'Syncing_Data_Stopping')
    PROVISIONING_TARGET_PAUSED = (33547, 'Provisioning_Target_Paused')
    FS_OK = (34048, 'FS_OK')
    FS_SOURCE_IO_FAILURE = (34049, 'FS_Source_IO_Failure')
    FS_DESTINATION_IO_FAILURE = (34050, 'FS_Destination_IO_Failure')
    FS_CONNECTION_FAILURE = (34051, 'FS_Connection_Failure')
    FS_UNRECOVERABLE_FAILURE = (34052, 'FS_Unrecoverable_Failure')
    VMO_FAULTED = (34304, 'VMO_Faulted')
    VMO_OFFLINE = (34305, 'VMO_Offline')
    ELEMENT_IMPORT_OK = (34560, 'Element_Import_OK')
    ELEMENT_IMPORT_UNABLE_TO_LOCATE_DEVICE = (
        34561, 'Element_Import_Unable_To_Locate_Device')
    ELEMENT_IMPORT_BAD_BLOCK_ON_SOURCE_DEVICE = (
        34562, 'Element_Import_Bad_Block_On_Source_Device')
    ELEMENT_IMPORT_UNABLE_TO_ACCESS_DEVICE = (
        34563, 'Element_Import_Unable_To_Access_Device')
    ELEMENT_IMPORT_LU_TRESPASSED = (34564, 'Element_Import_LU_Trespassed')
    ELEMENT_IMPORT_SOURCE_DEVICE_INACCESSIBLE = (
        34565, 'Element_Import_Source_Device_Inaccessible')
    ELEMENT_IMPORT_LOW_USER_LINK_BANDWIDTH = (
        34566, 'Element_Import_Low_User_Link_Bandwidth')
    ELEMENT_IMPORT_CONCURRENT_SANCOPY_SESSION_DESTINATIONS = (
        34567, 'Element_Import_Concurrent_SanCopy_Session_Destinations')
    ELEMENT_IMPORT_ERROR_COMMUNICATING_WITH_SANPVIEW = (
        34568, 'Element_Import_Error_Communicating_With_SanpView')
    ELEMENT_IMPORT_ERROR_COMMUNICATING_WITH_SANPVIEW_1 = (
        34569, 'Element_Import_Error_Communicating_With_SanpView_1')
    ELEMENT_IMPORT_SESSION_INCONSISTENT_STATE = (
        34570, 'Element_Import_Session_Inconsistent_State')
    ELEMENT_IMPORT_DESTINATION_INCONSISTENT_STATE = (
        34571, 'Element_Import_Destination_Inconsistent_State')
    ELEMENT_IMPORT_AUTO_RECOVERY_RESUME_FAILED = (
        34572, 'Element_Import_Auto_Recovery_Resume_Failed')
    ELEMENT_IMPORT_ALL_PATHS_FAILURE = (
        34573, 'Element_Import_All_Paths_failure')
    ELEMENT_IMPORT_ACCESS_DENIED_TO_DEVICE = (
        34574, 'Element_Import_Access_Denied_To_Device')
    ELEMENT_IMPORT_NOT_ENOUGH_MEMORY = (
        34575, 'Element_Import_Not_Enough_Memory')
    ELEMENT_IMPORT_SOURCE_DEVICE_FAILURE = (
        34576, 'Element_Import_Source_Device_Failure')
    ELEMENT_IMPORT_DESTINATION_DEVICE_FAILURE = (
        34577, 'Element_Import_Destination_Device_Failure')
    ELEMENT_IMPORT_DESTINATION_DEVICE_NOT_FOUND = (
        34578, 'Element_Import_Destination_Device_Not_found')
    ELEMENT_IMPORT_TARGET_LU_NOT_INITIALIZED = (
        34579, 'Element_Import_Target_LU_Not_Initialized')
    ELEMENT_IMPORT_COMMAND_TIMEDOUT = (
        34580, 'Element_Import_Command_TimedOut')
    ELEMENT_IMPORT_VERIFYING_FRONTEND_TIMEDOUT = (
        34581, 'Element_Import_Verifying_Frontend_TimedOut')
    ELEMENT_IMPORT_VERIFYING_FRONTEND_TIMEDOUT_ANOTHER_OPERATION = (
        34582, 'Element_Import_Verifying_Frontend_TimedOut_Another_Operation')
    ELEMENT_IMPORT_SOURCE_CONNECTIVITY_TIMEDOUT = (
        34583, 'Element_Import_Source_Connectivity_TimedOut')
    ELEMENT_IMPORT_DESTINATION_CONNECTIVITY_TIMEDOUT = (
        34584, 'Element_Import_Destination_Connectivity_TimedOut')
    ELEMENT_IMPORT_RLP_IO_FAILURE = (34585, 'Element_Import_RLP_IO_Failure')
    ELEMENT_IMPORT_TOTAL_SESSIONS_LIMIT_REACHED = (
        34586, 'Element_Import_Total_Sessions_Limit_Reached')
    ELEMENT_IMPORT_INCREMENTAL_SESSIONS_LIMIT_REACHED = (
        34587, 'Element_Import_Incremental_Sessions_Limit_Reached')
    ELEMENT_IMPORT_INCREMENTAL_SESSIONS_TOTAL_NUMBER_REACHED = (
        34588, 'Element_Import_Incremental_Sessions_Total_Number_Reached')
    ELEMENT_IMPORT_LIMIT_OF_TOTAL_SESSIONS_REACHED = (
        34589, 'Element_Import_Limit_Of_Total_Sessions_Reached')
    ELEMENT_IMPORT_LIMIT_OF_TOTAL_INCREMENTAL_SESSIONS_REACHED = (
        34590, 'Element_Import_Limit_Of_Total_Incremental_Sessions_Reached')
    ELEMENT_IMPORT_COPY_COMMAND_QUEUED = (
        34591, 'Element_Import_Copy_Command_Queued')
    ELEMENT_IMPORT_SESSION_FAILED_ON_SOURCE_OR_DESTINATION = (
        34592, 'Element_Import_Session_Failed_On_Source_Or_Destination')
    ELEMENT_IMPORT_DEVICE_CANNOT_BE_LOCATED = (
        34593, 'Element_Import_Device_Cannot_Be_Located')
    ELEMENT_IMPORT_NO_UNUSED_RLP_LUNS = (
        34594, 'Element_Import_No_Unused_Rlp_Luns')
    ELEMENT_IMPORT_RESERVED_LUN_NOT_SUPPORT_INCREMENTAL_SESSIONS = (
        34595, 'Element_Import_Reserved_Lun_Not_Support_Incremental_Sessions')
    ELEMENT_IMPORT_SNAPVIEW_RESERVED_LUN_NOT_ENOUGH_SPACE = (
        34596, 'Element_Import_Snapview_Reserved_Lun_Not_Enough_Space')
    ELEMENT_IMPORT_TOO_MANY_SNAPSHOTS_ON_SOURCE_LU = (
        34597, 'Element_Import_Too_Many_Snapshots_On_Source_Lu')
    ELEMENT_IMPORT_CANNOT_OPEN_RESERVED_LUN = (
        34598, 'Element_Import_Cannot_Open_Reserved_Lun')
    ELEMENT_IMPORT_CANNOT_GET_RESERVED_LUN_INFO = (
        34599, 'Element_Import_Cannot_Get_Reserved_Lun_info')
    ELEMENT_IMPORT_NO_SPACE_ON_RLP = (34600, 'Element_Import_No_Space_On_Rlp')
    ELEMENT_IMPORT_RLP_MAXIMUM_DEVICES = (
        34601, 'Element_Import_Rlp_Maximum_Devices')
    ELEMENT_IMPORT_SESSION_WITH_NO_CACHE_DEVICES = (
        34602, 'Element_Import_Session_With_No_Cache_Devices')
    ELEMENT_IMPORT_SESSION_FAILED_WRITE_TO_TARGET_INSUFFICIENT_STORAGE = (
        34603,
        'Element_Import_Session_Failed_Write_To_Target_Device_'
        'Insufficient_Storage')
    ELEMENT_IMPORT_SESSION_DEVICE_NOT_READY = (
        34604, 'Element_Import_Session_Device_Not_Ready')
    ELEMENT_IMPORT_SESSION_SOURCE_DEVICE_UNAVAILABLE = (
        34605, 'Element_Import_Session_Source_Device_Unavailable')
    ELEMENT_IMPORT_SESSION_SOURCE_IN_IMPORT_SESSION = (
        34606, 'Element_Import_Session_Source_In_Import_Session')


class ImportOpStatusEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return ImportOpStatusEnum


class ImportTypeEnum(UnityEnum):
    BLOCK = (0, 'block')
    NAS = (1, 'nas')


class PoolConsumerTypeEnum(UnityEnum):
    FILESYSTEM = (1, 'FileSystem')
    CONSISTENCYGROUP = (2, 'ConsistencyGroup')
    VMWARENFS = (3, 'VMwareNFS')
    VMWAREVMFS = (4, 'VMwareVMFS')
    LUN = (8, 'LUN')
    VVOLDATASTOREFS = (9, 'VVolDatastoreFS')
    VVOLDATASTOREISCSI = (10, 'VVolDatastoreISCSI')
    NASSERVER = (32768, 'NASServer')


class ImportStageEnum(UnityEnum):
    INITIAL = (0, 'Initial')
    INCREMENTAL = (1, 'Incremental')
    FINAL = (2, 'Final')


class DayOfWeekEnum(UnityEnum):
    SUNDAY = (1, 'Sunday')
    MONDAY = (2, 'Monday')
    TUESDAY = (3, 'Tuesday')
    WEDNESDAY = (4, 'Wednesday')
    THURSDAY = (5, 'Thursday')
    FRIDAY = (6, 'Friday')
    SATURDAY = (7, 'Saturday')


class DayOfWeekEnumList(UnityEnumList):
    @classmethod
    def get_enum_class(cls):
        return DayOfWeekEnum
