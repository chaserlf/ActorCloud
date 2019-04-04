import random
import string

from sqlalchemy import JSON, func
from sqlalchemy.dialects.postgresql import JSONB

from actor_libs.database.orm import BaseModel, ModelMixin, db
from actor_libs.utils import generate_uuid


__all__ = [
    'Client', 'ClientTag', 'Device', 'GroupDevices', 'Group', 'Product',
    'DeviceEvent', 'DeviceControlLog', 'DeviceConnectLog', 'GroupControlLog',
    'Policy', 'MqttAcl', 'Cert', 'CertAuth', 'MqttSub',
    'EmqxBill', 'EmqxBillHour', 'EmqxBillDay', 'EmqxBillMonth',
    'DeviceCountHour', 'DeviceCountDay', 'DeviceCountMonth',
    'UploadInfo', 'ProductGroupSub', 'Lwm2mObject', 'TimerPublish',
    'Lwm2mItem', 'Lwm2mInstanceItem', 'Lwm2mControlLog', 'Lwm2mSubLog',
    'ProductItem', 'Gateway', 'Channel'
]


def random_group_uid():
    """ Generate a 6-bit group identifier """

    group_uid = ''.join([
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    ])
    group = db.session.query(func.count(Group.id)) \
        .filter(Group.groupID == group_uid).scalar()
    if group:
        group_uid = random_group_uid()
    return group_uid


def random_product_uid():
    """ Generate a 6-bit product identifier """

    product_uid = ''.join([
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    ])
    product = db.session.query(func.count(Product.id)) \
        .filter(Product.productID == product_uid).scalar()
    if product:
        product_uid = random_product_uid()
    return product_uid


ClientTag = db.Table(
    'client_tags',
    db.Column('tagID', db.String(6), db.ForeignKey('tags.tagID'), primary_key=True),
    db.Column('deviceIntID', db.Integer,
              db.ForeignKey('clients.id', onupdate="CASCADE", ondelete="CASCADE"),
              primary_key=True)
)


class Client(BaseModel):
    __tablename__ = 'clients'
    deviceID = db.Column(db.String(50))  # 设备编号
    deviceName = db.Column(db.String(50))  # 设备名称
    softVersion = db.Column(db.String(50))  # 软件版本
    hardwareVersion = db.Column(db.String(50))  # 硬件版本
    manufacturer = db.Column(db.String(50))  # 制造商
    serialNumber = db.Column(db.String(100))  # 序列号
    location = db.Column(db.String(300))  # 安装位置
    longitude = db.Column(db.Float)  # 经度
    latitude = db.Column(db.Float)  # 纬度
    deviceUsername = db.Column(db.String(50))  # 设备用户名，用于连接emq
    token = db.Column(db.String(50), default=generate_uuid)  # 设备秘钥
    authType = db.Column(db.SmallInteger)  # 认证方式 1:Token 2:证书
    deviceStatus = db.Column(db.SmallInteger,
                             server_default='0')  # 设备运行状态 0:离线 1:在线 2:休眠
    deviceConsoleIP = db.Column(db.String(50))  # 控制台ip
    deviceConsoleUsername = db.Column(db.String(50))  # 控制台用户名
    deviceConsolePort = db.Column(db.Integer, server_default='22')  # 控制台端口
    upLinkSystem = db.Column(db.SmallInteger,
                             server_default='1')  # 上联系统 1:云 2:网关
    IMEI = db.Column(db.String(15))  # 设备IMEI
    IMSI = db.Column(db.String(100))  # 设备IMSI
    carrier = db.Column(db.Integer, server_default='1')  # 运营商
    physicalNetwork = db.Column(db.Integer, server_default='1')  # 物理网络
    blocked = db.Column(db.SmallInteger,
                        server_default='0')  # 是否允许访问 0:允许 1:禁止
    autoSub = db.Column(db.Integer)  # 自动订阅，0:关闭，1:开启
    description = db.Column(db.String(300))  # 描述
    mac = db.Column(db.String(50))  # mac地址：前端暂时没有设备mac地址，现在只网关mac地址
    type = db.Column(db.Integer)  # 类型：1设备，2网关
    tags = db.relationship('Tag', secondary=ClientTag,
                           backref=db.backref('devices', lazy='dynamic'))
    productID = db.Column(db.String, db.ForeignKey('products.productID'))  # 产品ID外键
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))  # 创建人ID外键
    tenantID = db.Column(db.String, db.ForeignKey('tenants.tenantID',
                                                  onupdate="CASCADE",
                                                  ondelete="CASCADE"))
    __mapper_args__ = {'polymorphic_on': type}


class Device(Client):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    deviceType = db.Column(db.SmallInteger,
                           server_default='1')  # 设备类型 1:终端 3:智能手机
    gateway = db.Column(db.Integer, db.ForeignKey('gateways.id'))  # 所属网关
    lora = db.Column(JSONB)
    modBusIndex = db.Column(db.SmallInteger)  # Modbus 协议设备索引
    metaData = db.Column(JSONB)  # 元数据
    parentDevice = db.Column(db.Integer,
                             db.ForeignKey('devices.id',
                                           onupdate="CASCADE",
                                           ondelete="CASCADE"))
    __mapper_args__ = {'polymorphic_identity': 1}


class Gateway(Client):
    __tablename__ = 'gateways'
    id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    gatewayModel = db.Column(db.String)  # 网关型号
    upLinkNetwork = db.Column(db.Integer)  # 上联网络
    devices = db.relationship('Device', foreign_keys="Device.gateway")  # 设备
    channels = db.relationship('Channel', foreign_keys="Channel.gateway")  # 通道
    __mapper_args__ = {'polymorphic_identity': 2}


GroupDevices = db.Table(
    'group_devices',
    db.Column('deviceID', db.String(100)),  # 设备ID
    db.Column('tenantID', db.String(100)),  # 租户ID
    db.Column('groupID', db.String(6),
              db.ForeignKey('groups.groupID', onupdate="CASCADE", ondelete="CASCADE")),
    db.Column('deviceIntID', db.Integer, db.ForeignKey('clients.id')),
)


class Group(BaseModel):
    __tablename__ = 'groups'
    groupID = db.Column(db.String(6),
                        default=random_group_uid, unique=True)  # 分组标识
    groupName = db.Column(db.String(50))
    description = db.Column(db.String(300))
    productID = db.Column(db.String,
                          db.ForeignKey('products.productID'))  # 产品ID外键
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))
    devices = db.relationship('Client', secondary=GroupDevices,
                              backref=db.backref('groups', lazy='dynamic'), lazy='dynamic')


class Product(BaseModel):
    """
    cloudProtocol(云端协议): 1:MQTT，2:CoAp，3:LwM2M，4:LoRaWAN，5:HTTP，6:WebSocket
    """
    __tablename__ = 'products'
    productID = db.Column(db.String(6), default=random_product_uid, unique=True)  # 产品标识
    productName = db.Column(db.String(50))  # 产品名称
    description = db.Column(db.String(300))  # 产品描述
    cloudProtocol = db.Column(db.SmallInteger, server_default='1')  # 云端协议, 网关类型产品显示为上联协议
    gatewayProtocol = db.Column(db.Integer)  # 网关协议
    productType = db.Column(db.SmallInteger, server_default='1')  # 产品类型 1:设备，2:网关
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))
    devices = db.relationship('Client', backref='products', lazy='dynamic')


class DeviceEvent(ModelMixin, db.Model):
    """ 设备上行消息 """
    __tablename__ = 'device_events'
    __table_args__ = (
        db.Index('device_events_msgTime_idx', "msgTime"),
    )
    msgTime = db.Column(db.DateTime, primary_key=True)  # 消息时间
    tenantID = db.Column(db.String(9), primary_key=True)
    productID = db.Column(db.String(6))
    deviceID = db.Column(db.String(100), primary_key=True)  # 设备uid
    topic = db.Column(db.String(500))  # 主题
    payload_string = db.Column(db.String(100000))  # 原始的 payload
    payload_json = db.Column(JSONB)  # 处理后的 payload


class DeviceConnectLog(BaseModel):
    """ 设备连接日志 """
    __tablename__ = 'device_connect_logs'
    createAt = db.Column(db.DateTime, server_default=func.now())
    connectStatus = db.Column(db.SmallInteger)  # 事件 0:下线 1:上线 2:认证失败
    IP = db.Column(db.String(50))  # 连接IP
    deviceID = db.Column(db.String(100))  # 设备uid
    keepAlive = db.Column(db.Integer)  # 心跳时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"))  # 租户UID


class DeviceControlLog(BaseModel):
    """
    设备控制日志
    * controlType 控制类型: 1 消息下发，2 读 3 写 4 执行
    * publishStatus: 0 失败 1 已下发 2 已到达
    """

    __tablename__ = 'device_control_logs'
    path = db.Column(db.String(500))  # lwm2m path
    topic = db.Column(db.String(500))  # mqtt topic
    taskID = db.Column(db.String(64), unique=True)  # 设备下发消息任务
    controlType = db.Column(db.SmallInteger, server_default='1')  # 控制类型
    payload = db.Column(JSONB)  # 设备下发消息内容
    publishStatus = db.Column(db.SmallInteger)  # 下发状态
    userIntID = db.Column(db.Integer,
                          db.ForeignKey('users.id',
                                        onupdate="CASCADE", ondelete="CASCADE"))  # 用户id
    deviceIntID = db.Column(db.Integer,
                            db.ForeignKey('clients.id',
                                          onupdate="CASCADE", ondelete="CASCADE"))  # 设备id
    groupControlLogIntID = db.Column(db.Integer,
                                     db.ForeignKey('group_control_logs.id',
                                                   onupdate="CASCADE", ondelete="CASCADE"))


class GroupControlLog(BaseModel):
    """
    设备控制日志
    * controlType 控制类型: 1 消息下发，2 读 3 写 4 执行
    * publishStatus: 0 失败 1 已下发 2 已到达
    """

    __tablename__ = 'group_control_logs'
    path = db.Column(db.String(500))  # lwm2m path
    topic = db.Column(db.String(500))  # mqtt topic
    taskID = db.Column(db.String(64), unique=True)  # 设备下发消息任务ID
    controlType = db.Column(db.SmallInteger, server_default='1')  # 控制类型
    payload = db.Column(JSONB)  # payload
    publishStatus = db.Column(db.SmallInteger, default=0)  # 状态 0 失败 1 成功
    groupID = db.Column(db.String, db.ForeignKey(
        'groups.groupID', onupdate="CASCADE", ondelete="CASCADE"))  # 分组 uid
    userIntID = db.Column(db.Integer,
                          db.ForeignKey('users.id',
                                        onupdate="CASCADE", ondelete="CASCADE"))  # 用户 id


class Policy(BaseModel):
    __tablename__ = 'policies'
    name = db.Column(db.String(50))  # 名称
    access = db.Column(db.SmallInteger)  # 操作
    allow = db.Column(db.SmallInteger)  # 访问控制
    description = db.Column(db.String(300))  # 描述
    topic = db.Column(db.String(500))  # 主题
    mqtt_acl = db.relationship('MqttAcl',
                               backref='policies',
                               passive_deletes=True,
                               lazy=True)
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))  # 用户id


class MqttAcl(BaseModel):
    __tablename__ = 'mqtt_acl'
    ipaddr = db.Column(db.String(50))  # ip地址
    allow = db.Column(db.SmallInteger)  # 访问控制
    username = db.Column(db.String(100))  # 名称
    access = db.Column(db.SmallInteger)  # 操作
    clientID = db.Column(db.String(100))  # 客户端uid tenantID:productID:deviceID
    topic = db.Column(db.String(500))  # 主题
    deviceIntID = db.Column(db.Integer, db.ForeignKey(
        'clients.id', onupdate="CASCADE", ondelete="CASCADE"))  # 设备id
    policyIntID = db.Column(db.Integer, db.ForeignKey(
        'policies.id', onupdate="CASCADE", ondelete="CASCADE"))  # 策略 id


class Cert(BaseModel):
    __tablename__ = 'certs'
    name = db.Column(db.String)
    enable = db.Column(db.SmallInteger, default=1)  # 是否可用
    CN = db.Column(db.String(36), unique=True)
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))
    key = db.Column(db.String(2000))  # key file string
    cert = db.Column(db.String(2000))  # cert file string


class CertAuth(BaseModel):
    __tablename__ = 'cert_auth'
    enable = db.Column(db.SmallInteger, default=1)  # 是否可用
    clientID = db.Column(db.String(100))  # tenantID:productID:deviceID
    deviceIntID = db.Column(db.Integer,
                            db.ForeignKey('clients.id', onupdate="CASCADE", ondelete="CASCADE"))
    CN = db.Column(db.String,
                   db.ForeignKey('certs.CN',
                                 onupdate="CASCADE", ondelete="CASCADE"))


class MqttSub(BaseModel):
    __tablename__ = 'mqtt_sub'
    clientID = db.Column(db.String(100))
    topic = db.Column(db.String(500))
    qos = db.Column(db.SmallInteger, default=1)
    deviceIntID = db.Column(db.Integer, db.ForeignKey(
        'clients.id', onupdate="CASCADE", ondelete="CASCADE"))


EmqxBill = db.Table(
    'emqx_bills',
    db.Column('msgTime', db.DateTime, nullable=False),  # 消息时间
    db.Column('tenantID', db.String(9)),  # 租户ID
    db.Column('productID', db.String(6)),  # 产品 ID
    db.Column('deviceID', db.String(100)),  # 设备ID
    db.Column('msgType', db.SmallInteger),  # 1登录，2订阅，3取消订阅，4发布，5接收
    db.Column('msgSize', db.Integer),  # 消息大小
    db.Index('emqx_bills_msgTime_idx', 'msgTime'),
    db.Index('emqx_bills_union_idx', 'msgTime', 'tenantID', 'deviceID', 'msgType')
)


class EmqxBillHour(ModelMixin, db.Model):
    __tablename__ = 'emqx_bills_hour'
    __table_args__ = (
        db.Index('emqx_bills_hour_countTime_idx', "countTime"),
    )
    msgType = db.Column(db.Integer, primary_key=True)  # 消息类型
    msgCount = db.Column(db.Integer)  # 小时消息数量
    msgSize = db.Column(db.Integer)  # 小时消息流量
    countTime = db.Column(db.DateTime, primary_key=True)  # 统计时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)


class EmqxBillDay(BaseModel):
    __tablename__ = 'emqx_bills_day'
    msgType = db.Column(db.Integer)  # 消息类型
    msgCount = db.Column(db.Integer)  # 小时消息数量
    msgSize = db.Column(db.Integer)  # 小时消息流量
    countTime = db.Column(db.DateTime)  # 统计时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"))


class EmqxBillMonth(BaseModel):
    __tablename__ = 'emqx_bills_month'
    msgType = db.Column(db.Integer)  # 消息类型
    msgCount = db.Column(db.Integer)  # 月消息数量
    msgSize = db.Column(db.Integer)  # 月消息流量
    countTime = db.Column(db.DateTime)  # 统计时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"))


class DeviceCountHour(BaseModel):
    __tablename__ = 'device_count_hour'
    deviceCount = db.Column(db.Integer)  # 小时设备数量
    deviceOnlineCount = db.Column(db.Integer)  # 小时设备在线数量
    deviceOfflineCount = db.Column(db.Integer)  # 小时离线设备数量
    deviceSleepCount = db.Column(db.Integer)  # 休眠设备数
    countTime = db.Column(db.DateTime)  # 统计时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"))


class DeviceCountDay(BaseModel):
    ___tablename__ = 'device_count_day'
    deviceCount = db.Column(db.Integer)  # 日设备数量
    deviceOnlineCount = db.Column(db.Integer)  # 日在线数量
    deviceOfflineCount = db.Column(db.Integer)  # 日设备数量
    deviceSleepCount = db.Column(db.Integer)  # 休眠设备数
    countTime = db.Column(db.DateTime)  # 统计时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"))


class DeviceCountMonth(BaseModel):
    __tablename__ = 'device_count_month'
    deviceCount = db.Column(db.Integer)  # 月设备数量
    deviceOnlineCount = db.Column(db.Integer)  # 日设备在线数量
    deviceOfflineCount = db.Column(db.Integer)  # 日离线设备数量
    deviceSleepCount = db.Column(db.Integer)  # 休眠设备数
    countTime = db.Column(db.DateTime)  # 统计时间
    tenantID = db.Column(db.String, db.ForeignKey(
        'tenants.tenantID', onupdate="CASCADE", ondelete="CASCADE"))


class UploadInfo(BaseModel):
    __tablename__ = 'upload_info'
    fileName = db.Column(db.String(300))  # 文件名称
    displayName = db.Column(db.String(300))  # 文件原始名称
    fileType = db.Column(db.SmallInteger, default=1)  # 文件类型：1压缩包, 2图片
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))  # 创建人ID外键


class TimerPublish(BaseModel):
    __tablename__ = 'timer_publish'
    taskName = db.Column(db.String)  # 任务名
    taskStatus = db.Column(db.SmallInteger, server_default='2')  # 任务状态 2 执行 3 成功
    timerType = db.Column(db.SmallInteger)  # 定时类型 1 固定 , 2 间隔
    publishType = db.Column(db.SmallInteger)  # 0 设备下发, 1 分组下发
    controlType = db.Column(db.SmallInteger)  # 下发类型
    topic = db.Column(db.String(500))  # 主题(mqtt)
    path = db.Column(db.String(500))  # lwm2m path
    payload = db.Column(JSONB)  # 下发消息内容
    intervalTime = db.Column(JSONB)  # 间隔时间 {'weekday': 'hour': 'minute'}
    crontabTime = db.Column(db.DateTime)  # 指定下发时间
    groupID = db.Column(db.String, db.ForeignKey(
        'groups.groupID', onupdate="CASCADE", ondelete="CASCADE"))  # 分组 uid
    deviceIntID = db.Column(db.Integer, db.ForeignKey(
        'clients.id', onupdate="CASCADE", ondelete="CASCADE"))  # 设备id
    userIntID = db.Column(db.Integer, db.ForeignKey(
        'users.id', onupdate="CASCADE", ondelete="CASCADE"))  # 用户


class ProductGroupSub(BaseModel):
    __tablename__ = 'product_group_sub'
    topic = db.Column(db.String(500))  # 主题
    qos = db.Column(db.SmallInteger, default=1)
    productIntID = db.Column(db.Integer, db.ForeignKey(
        'products.id', onupdate="CASCADE", ondelete="CASCADE"))
    groupIntID = db.Column(db.Integer, db.ForeignKey(
        'groups.id', onupdate="CASCADE", ondelete="CASCADE"))


class Lwm2mObject(BaseModel):
    __tablename__ = 'lwm2m_objects'
    objectName = db.Column(db.String)  # 对象名
    objectID = db.Column(db.Integer, unique=True)  # 对象int型ID
    description = db.Column(db.String)  # 对象描述
    objectURN = db.Column(db.String)  # 对象URN
    objectVersion = db.Column(db.String)  # 对象版本
    multipleInstance = db.Column(db.String)  # Multiple表示有多个实例，Single表示单个实例
    mandatory = db.Column(db.String)  # 强制性，Optional表示可选，Mandatory表示强制


class Lwm2mItem(BaseModel):
    __tablename__ = 'lwm2m_items'
    itemName = db.Column(db.String)  # 属性名
    itemID = db.Column(db.Integer)  # 属性int型ID
    objectItem = db.Column(db.String)  # /objectID/itemID
    description = db.Column(db.String)  # 属性描述
    itemType = db.Column(db.String)  # 属性类型
    itemOperations = db.Column(db.String)  # 支持操作，R/W/RW/E
    itemUnit = db.Column(db.String)  # 单位
    rangeEnumeration = db.Column(db.String)  # 属性的值范围
    mandatory = db.Column(db.String)  # 强制性，Optional表示可选，Mandatory表示强制
    multipleInstance = db.Column(db.String)  # Multiple表示有多个实例，Single表示单个实例
    objectID = db.Column(db.Integer,
                         db.ForeignKey('lwm2m_objects.objectID',
                                       onupdate="CASCADE",
                                       ondelete="CASCADE"))


class Lwm2mInstanceItem(BaseModel):
    __tablename__ = 'lwm2m_instance_items'
    instanceID = db.Column(db.Integer)  # 实例int型ID
    objectAutoSub = db.Column(db.Integer, server_default='0')  # 对象自动订阅
    itemAutoSub = db.Column(db.Integer, server_default='0')  # 属性自动订阅
    path = db.Column(db.String)  # 属性地址
    deviceIntID = db.Column(db.Integer,
                            db.ForeignKey('clients.id',
                                          onupdate="CASCADE", ondelete="CASCADE"))
    objectID = db.Column(db.Integer,
                         db.ForeignKey('lwm2m_objects.objectID',
                                       onupdate="CASCADE", ondelete="CASCADE"))
    itemIntID = db.Column(db.Integer,
                          db.ForeignKey('lwm2m_items.id',
                                        onupdate="CASCADE", ondelete="CASCADE"))
    productID = db.Column(db.String,
                          db.ForeignKey('products.productID',
                                        onupdate="CASCADE", ondelete="CASCADE"))
    tenantID = db.Column(db.String,
                         db.ForeignKey('tenants.tenantID',
                                       onupdate="CASCADE", ondelete="CASCADE"))


class Lwm2mControlLog(BaseModel):
    __tablename__ = 'lwm2m_control_logs'
    payload = db.Column(JSON)  # 推送消息内容
    instanceItemIntID = db.Column(db.Integer,
                                  db.ForeignKey('lwm2m_instance_items.id',
                                                onupdate="CASCADE",
                                                ondelete="CASCADE"))
    publishStatus = db.Column(db.SmallInteger, default=1)  # 状态
    publishType = db.Column(db.String(100))  # 推送类型
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))
    taskID = db.Column(db.String(100), unique=True)  # 设备下发消息任务ID


class Lwm2mSubLog(BaseModel):
    __tablename__ = 'lwm2m_sub_logs'
    deviceIntID = db.Column(db.Integer,
                            db.ForeignKey('clients.id',
                                          onupdate="CASCADE", ondelete="CASCADE"))
    tenantID = db.Column(db.String,
                         db.ForeignKey('tenants.tenantID',
                                       onupdate="CASCADE",
                                       ondelete="CASCADE"))

    payload = db.Column(JSON)  # 推送消息内容
    objectID = db.Column(db.Integer,
                         db.ForeignKey('lwm2m_objects.objectID',
                                       onupdate="CASCADE",
                                       ondelete="CASCADE"))
    instanceItemIntID = db.Column(db.Integer,
                                  db.ForeignKey('lwm2m_instance_items.id',
                                                onupdate="CASCADE",
                                                ondelete="CASCADE"))
    publishStatus = db.Column(db.SmallInteger, default=1)  # 状态
    publishType = db.Column(db.String(100))  # 推送类型
    userIntID = db.Column(db.Integer, db.ForeignKey('users.id'))
    taskID = db.Column(db.String(100), unique=True)  # 设备订阅任务ID


class ProductItem(BaseModel):
    __tablename__ = 'product_items'
    itemIntID = db.Column(db.Integer,
                          db.ForeignKey('lwm2m_items.id',
                                        onupdate="CASCADE",
                                        ondelete="CASCADE"))
    objectID = db.Column(db.Integer,
                         db.ForeignKey('lwm2m_objects.objectID',
                                       onupdate="CASCADE",
                                       ondelete="CASCADE"))
    itemID = db.Column(db.Integer)  # 属性ID
    productID = db.Column(db.String,
                          db.ForeignKey('products.productID',
                                        onupdate="CASCADE",
                                        ondelete="CASCADE"))  # 产品ID外键
    tenantID = db.Column(db.String,
                         db.ForeignKey('tenants.tenantID',
                                       onupdate="CASCADE",
                                       ondelete="CASCADE"))


class Channel(BaseModel):
    __tablename__ = 'channels'
    channelType = db.Column(db.String)  # 通道类型， 1:COM，2:TCP
    drive = db.Column(db.String)  # 网关驱动
    COM = db.Column(db.String)  # COM
    Baud = db.Column(db.Integer)  # Baud
    Data = db.Column(db.Integer)  # 6/7/8
    Stop = db.Column(db.String)  # 1/1.5/2
    Parity = db.Column(db.String)  # N/O/E
    IP = db.Column(db.String)  # TCP, 服务器ip
    Port = db.Column(db.Integer)  # TCP, 端口
    gateway = db.Column(db.Integer, db.ForeignKey('gateways.id'))