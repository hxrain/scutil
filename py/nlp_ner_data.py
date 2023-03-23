from enum import Enum, unique
from collections.abc import Iterable
from copy import deepcopy

'''
    NT组份类别:
        NF 前导冠字 - 中国/中共/国网/国电
        NS 行政区划 - 北京市/北京/黑龙江省/黑龙江/哈尔滨香坊区/(香港)/(南京)
        NN 字号名称 - 中招国联/华为/新中新/海能达
        NZ 行业特征 - 科技/技术/信息/门业/机械
        NM 组织形式 - 公司/有限公司/有限责任公司/俱乐部/厂/场/宫/店/委员会/办公室
        NO 单字模式 - 厂/处/院/馆
           分支特征 - 中山路/大王村/第二/三十五
        NB 分支机构 - 分公司/分店/分厂
        NL 后置冠字 - (普通合伙)/(有限公司)/(特殊合伙)/(有限责任公司)/(协会)

'''


@unique
class types(Enum):
    '''根据常用尾缀进行NT行业类型划分'''
    # 组织形式对应的可能行业类别
    com = 1  # 商业公司
    gov = 2  # 政府机构
    mining = 3  # 采矿业
    retail = 4  # 批零业
    catering = 5  # 餐饮业
    tourism = 6  # 旅游业
    amuse = 7  # 娱乐业
    service = 8  # 服务业
    relig = 9  # 宗教
    cultural = 10  # 文艺
    traffic = 11  # 交通运输
    communica = 12  # 通信业
    financial = 13  # 金融业
    postal = 14  # 邮政业
    fishery = 15  # 水产渔业
    industry = 16  # 工业
    gardening = 17  # 园林绿化
    farming = 18  # 农业种植业
    logistics = 19  # 物流仓储业
    individual = 20  # 个体户
    org = 21  # 团体组织
    env = 22  # 环保产业
    medical = 23  # 医疗
    sports = 24  # 体育运动
    construct = 25  # 建筑建造
    tech = 26  # 科技行业
    judicial = 27  # 司法机关
    breeding = 28  # 养殖业
    irrigation = 29  # 水利
    energy = 30  # 能源
    edu = 31  # 教育行业

    # NT组份类别
    NF = 100  # 前导冠字
    NC = 101  # 企业名称单字
    NO = 102  # 组织机构的单字尾缀
    ND = 103  # 单字尾缀规避词
    NU = 104  # 数字与序数
    NN = 105  # 企业名称字号
    NZ = 150  # 专用名词,业务词
    NM = 160  # 组织形式
    NB = 170  # 分支机构
    NL = 180  # 后置冠字

    NS = 110  # 地点/地区名称
    NS1 = 111  # 地区名称,省/直辖市
    NS2 = 112  # 地区名称,地市州盟
    NS3 = 113  # 地区名称,区县旗
    NS4 = 114  # 地区名称,乡
    NS5 = 115  # 地区名称,镇
    NS6 = 116  # 地区名称,村
    NS7 = 117  # 地区名称,地标/街路楼/景区

    # 统一定义的人名组份类别
    NR = 120  # 完整人名,或常见的不含姓氏的名字部分
    NR1 = 121  # 人名单字姓氏
    NR2 = 122  # 人名双字复姓
    NR3 = 123  # 人名多字姓氏

    # NT层级
    LV0 = 200  # 组织层级0 - 全国性的集团总公司/国家级政府机构(部/司)
    LV1 = 201  # 组织层级1 - 公司主体/组织核心/省市区县级的行政机构(厅/处/局)
    LV2 = 202  # 组织层级2 - 分公司/分厂/村镇级行政机构(科/室/站)
    LV3 = 203  # 组织层级3 - 个体经营摊点/小微组织

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    @staticmethod
    def type_by_num(num):
        """根据数字查找对应的主要组份类别"""
        assert num >= types.NF.value
        if types.NS1.value <= num <= types.NS7.value:
            return types.NS
        if types.NR.value <= num <= types.NR3.value:
            return types.NR
        return types(num)

    @staticmethod
    def type(val):
        if isinstance(val, Iterable):
            val = max(val)
        if isinstance(val, types):
            return types.type_by_num(val.value)
        else:
            return types.type_by_num(val)

    @staticmethod
    def trade(tags):
        """挑选出tags集合中的行业类别"""
        rst = []
        for t in tags:
            if t.value < types.NF.value and t not in rst:
                rst.append(t)
        return rst

    @staticmethod
    def equ(v, t):
        """判断给定的值v是否等同于指定的主要类型type"""

        def make_set(val):
            if isinstance(val, Iterable):
                val = max(val)
            if val.value < types.NF.value:
                return set()
            return {types.type(val.value)}

        if isinstance(v, types):
            return types.type(v.value) == types.type(t.value)
        elif isinstance(v, Iterable):
            set_t = make_set(t)
            set_v = make_set(v)
            if not set_t.isdisjoint(set_v):
                return True
        elif isinstance(v, int):
            return types.type(v) == types.type(t)
        return False


# 常见NT组织形式描述
nt_tails = {
    # 工矿企业
    '分店': {'.': {types.NB}, '-': {},
           '+': {'分号', '分厂', '分矿', '分校', '分公司', '分司', '分工司', '支公司', '分部', '分局', '分院', '分所', '直属分局', '支局', '分园', '子厂', '分场', '分社',
                 '分站', "分会", "子站", "分支机构", "分队", "分处", }},
    '工厂': {'.': {types.NM, types.industry}, '-': {},
           '+': {'加工厂', '化工厂', '学区', '工区', '校区', '灌区', '件厂', '剂厂', '布厂', '床厂', '总厂', '机厂', '材厂', '板厂', '水厂', '油厂', '泵厂', '工廠',
                 '炉厂', '煤厂', '瓦厂', '瓷厂', '石厂', '砖厂', '管厂', '箱厂', '粉厂', '纸厂', '织厂', '肥厂', '胶厂', '船厂', '茶厂', '药厂', '表厂', '内衣廠',
                 '车厂', '酒厂', '钢厂', '铁厂', '门厂', '鞋厂', '配件厂', '建材厂', '自来水厂', '修理厂', '汽车修理厂', '汽修厂', '维修厂', '开关厂', '家具厂', "服饰厂",
                 '工具厂', '模具厂', '玩具厂', '预制厂', '印刷厂', '彩印厂', '制品厂', '用品厂', '艺品厂', '食品厂', '仪器厂', '电器厂', '设备厂', '塑料厂', '材料厂', "漆厂",
                 '涂料厂', '石料厂', '机械厂', '水泥厂', '处理厂', '门窗厂', '电缆厂', '工艺厂', '制衣厂', '包装厂', '服装厂', '修造厂', '制造厂', '铸造厂', '修配厂', '五金厂',
                 "丝厂", "大修厂", "家俱厂", "灯具厂", "皮具厂", "福利厂", "箱包厂", "综合厂", "纸品厂", "木器厂", "屠宰厂", "饮料厂", "饲料厂", "结构厂", "气厂", "灰厂", "冶炼厂",
                 "标牌厂", "玻璃厂", "矿厂", "选矿厂", "砂厂", "米厂", "线厂", "网厂", "花厂", "袋厂", "选厂", "再选厂", "冶选厂", "分选厂", "生产厂", "机修厂", "冷冻厂", "雕刻厂",
                 "焦化厂", "沙发厂", "绣品厂", "饰品厂", "变压器厂", "垫厂", "手套厂", "轴承厂", "维护厂", "辅料厂", "设施厂", "木厂", "电杆厂", "架厂", "柜厂", "器械厂", "医疗器械厂",
                 "灯厂", "烟厂", "卷烟厂", "球厂", "家私厂", "窑厂", "轮窑厂", "弹簧厂", "纺厂", "毛衫厂", "羊毛衫厂", "轮厂", "织造厂", "锻造厂", "合金厂", "锌厂", "电镀厂", "灯饰厂",
                 "香厂", "实验厂", }},
    '电厂': {'.': {types.NM, types.energy}, '-': {},
           '+': {'发电厂', '电站', '发电站', '水电站', '核电站', '供电局', '供电所', "风电场"}},
    '公司': {'.': {types.NM, types.com}, '-': {},
           '+': {'企业', '总公司', '有限公司', '有限责任公司', '责任公司', '股份公司', '集团公司', '集团有限公司', '集团有限责任公司', '集团总公司', '株式会社', '顾问有限公司',
                 '服务公司', '工程公司', '业有限公司', '实业有限公司', '股份有限公司', '保险股份有限公司', '开发有限公司', '科技开发有限公司', '设备有限公司', '发展有限公司',
                 '建设发展有限公司', '科技有限公司', '智能科技有限公司', '管理有限公司', '工程有限公司', '设计有限公司', '建设有限公司', '制造有限公司', 'LTD.', 'LTD',
                 '经纪有限公司', '劳司', '工司', '有限责任工司'}},
    '集团': {'.': {types.NM, types.com}, '-': {},
           '+': {'产业集团', '企业集团', '实业集团', '置业集团', '药业集团', '地产集团', '房地产集团', '开发集团', '食品集团', '电器集团', '发展集团', '建工集团', '新华书店集团',
                 '技术集团', '建材集团', '路桥集团', '机械集团', '电气集团', '物流集团', '能源集团', '管理集团', '工程集团', '建筑集团', '电缆集团', '控股集团', '投资控股集团',
                 '教育集团', '建设集团', '市政建设集团', '商贸集团', '投资集团', '国际集团', '粮食集团', '装饰集团'}},
    '中心': {'.': {types.NM, types.gov, types.service}, '-': {'心里', '心理', '心中', '心智', '心情', '心思', '心脏', '心脑', '心内', '心外'},
           '+': {'服务中心', '管理中心', '培训中心', '运动中心'}},
    '矿区': {'.': {types.NM, types.mining}, '-': {},
           '+': {'矿井', '煤矿', '矿山', '金矿', '铁矿', '气矿', '盐矿', '石矿', '砂矿', '硅矿', '钙矿', '钛矿', '钨矿', '铅矿', '钼矿', '铀矿', '铜矿', '铝矿', '锡矿',
                 '锌矿', '锰矿', '联营矿', '金属矿', '原料矿', '有色矿', '露天矿', '石灰石矿山', '重晶石矿山'}, '-': {'采矿', '探矿', '洗矿', '矿长', }},
    '工坊': {'.': {types.NM, types.industry}, '-': {},
           '+': {'油坊', '磨坊', '酒坊', "作坊", "烘焙坊", }},
    '工场': {'.': {types.NM, types.industry}, '-': {},
           '+': {'总场', '梁场', '沙场', '煤场', '盐场', '石场', '砂场', '加工场', '屠宰场', '制梁场', '采石场', '停车场', '停车埸', '洗车场', '加工埸', "料场", "预制场", }},
    '基地': {'.': {types.NM, types.service}, '-': {},
           '+': {'训练基地', '活动营地', '露营地', '单车营', '大本营', '应急营', '成长营', '服务营', '渡假营', '训练营'}},
    '合伙': {'.': {types.NM, types.com}, '-': {'合伙人'},
           '+': {'管理合伙', '咨询合伙', '农业合伙', '有限合伙', '房地产合伙', '投资合伙', '普通合伙'}},
    '联盟': {'.': {types.NM, types.com}, '-': {''},
           '+': {'产业技术联盟', '产业联盟', '公益联盟', '创业联盟', '创新战略联盟', '创新联盟', '剧院联盟', '博物馆联盟', '发展联盟', '合作联盟', '图书馆联盟', '幸福联盟',
                 '志愿者联盟', '战略联盟', '技术创新战略联盟', '技术创新联盟', '技术联盟', '投资联盟', '教育联盟', '旅游联盟', '智库联盟', '服务联盟', '爱心联盟', '贸易联盟',
                 '阳光志愿者联盟', '国际联盟', '产学研资联盟', '采购联盟', '认证联盟', '建设联盟', '培训联盟', '演艺联盟', '孝老联盟', '网络联盟', '组织联盟', '应用联盟',
                 '品牌联盟', '产权联盟', '文旅联盟', '开放联盟', '党建联盟', '义工联盟', '家居联盟', '企业家联盟', '创客联盟', '基地联盟', '生态圈联盟', '互助联盟', '电子商务联盟',
                 '众创联盟', '振兴联盟', '办公联盟', '新媒体联盟', '评价联盟', '行业联盟', '企业联盟', '(企业)联盟'}},
    '服务机构': {'.': {types.NM, types.com}, '-': {},
             '+': {'产品认证服务机构', '会展策划机构', '传媒机构', '传播机构', '制漆机构', '办事机构', '动画机构', '咨询机构', '品牌推广机构', '培训机构', '广告传媒机构',
                   '开发机构', '影视动画机构', '影视机构', '托管机构', '推广机构', '摄影机构', '摄影设计机构', '教育咨询机构', '教育机构', '数码影视动画机构', '校外托管机构',
                   '潜能教育机构', '策划机构', '美体机构', '美发机构', '认证服务机构'}},

    '砖窑': {'.': {types.NM, types.industry}, '-': {},
           '+': {'瓦窑', '石灰窑', '砖瓦窑', '灰窑', '焖窑', '煤窑'}},
    '回收站': {'.': {types.NM, types.env}, '-': {},
            '+': {'回收', '回收拆解站', '回收处', '回收厂', '回收点', '回收行', '回收中心', '回收部', '回收利用部', '回收利用站', '回收店', '回收队', '废品回收',
                  '物质回收', '资源回收', '物资回收', '再生资源回收', '收购站', '废品收购站', }},
    # 政府司法
    '法院': {'.': {types.NM, types.gov, types.judicial}, '-': {},
           '+': {'仲裁庭', '审判庭', '法庭', '人民法院', '中级人民法院', '高级人民法院', '检察院', '仲裁院', '争议仲裁院', '执行庭'}},
    '公安局': {'.': {types.NM, types.gov, types.judicial}, '-': {},
            '+': {'司法局', '审计局', '监察局', '监察大队', '交通警察支队', '警察大队', '交通警察大队', '公安厅', '派出所', '看守所', '司法所',
                  '戒毒所', '鉴定所', '司法鉴定所', '监狱', "拘留所", }},
    '政府': {'.': {types.NM, types.gov}, '-': {'关于'},
           '+': {'人民政府', '机关', '海关', '办事处', '街道办事处', "商务部", }},
    '办公厅': {'.': {types.NM, types.gov}, '-': {},
            '+': {'贸易经济合作厅', '财政厅', '自然资源厅', '自然资源和规划厅', '经济和信息化厅', '经济合作厅', '管理厅', '科技厅', '科学技术厅', '社会保障厅', '监督管理厅',
                  '生态环境厅', '环境生态厅', '环境保护厅', '环保厅', '渔业厅', '海洋与渔业厅', '水利厅', '民政厅', '文化广电出版体育厅', '文化和旅游厅', '文化和新闻出版厅',
                  '文化厅', '文化传播厅', '教育厅', '建设厅', '应急管理厅', '广电出版体育厅', '工业和信息化厅', '对外贸易经济合作厅', '审计厅', '国土资源厅', '司法厅',
                  '劳动和社会保障厅', '农牧业厅', '农牧厅', '农业厅', '农业农村厅', '信息产业厅', '保障厅', '住房和城乡建设厅', '交通运输厅', '交通厅'}},
    '办公室': {'.': {types.NM, types.gov}, '-': {},
            '+': {'管理办公室', '项目办公室', '研究室', '教学研究室', '政策研究室', '工作办', '法制办', '开发办', '综合开发办', '政府办', '接待办', '管理办',
                  '建设管理办', '领导小组办', '建设办', }},
    # 学校
    '幼儿园': {'.': {types.NM, types.edu}, '-': {},
            '+': {'幼稚园', '机关幼儿园', '附属幼儿园', '中心幼儿园', '午托', '午托班', '幼儿班', '托管班', '托育班', '看护班', }},
    '培训班': {'.': {types.NM, types.edu}, '-': {},
            '+': {'委托班', '教学班', '补习班', '训练班', '辅导班', "讲师团", }},
    '学校': {'.': {types.NM, types.edu}, '-': {},
           '+': {'小学', '小学校', '中学', '中学校', '高中', '中心校', '总校', '中心学校', '武校', '盲校', '网校', '聋校', '联校', '公学', '职业中学', '附属中学',
                 '民族中学', '初级中学', '高级中学', '职业高级中学', '实验中学', '中小学', '完全小学', '附属小学', '中心小学', '民族小学', '实验小学', '初级中学校',
                 '高级中学校', '进修学校', '实验小学校', '实验学校', '学园', '附小', '完小', '师范附小', '初中', '实验初中', '附属初中'}},
    '职校': {'.': {types.NM, types.edu}, '-': {},
           '+': {'艺校', '驾校', '进修校', '体校', '技校', '鼓校', '业校', '中专', '职业中专', '卫校', '农校', '农广校', '农机校', '联合校', '技工学校', '技术学校',
                 '艺术学校', '卫生学校', '培训学校', '中专学校', '工业学校', '老年大学', '党校', '团校', '专科学校', '干部学校', '区委党校', '县委党校', '市委党校',
                 '专科', '高等专科', '医专', '行政管理学校'}},
    '大学': {'.': {types.NM, types.edu}, '-': {},
           '+': {'理工大学', '科技大学', '医科大学', '师范大学', '中医药大学', '电视大学', '交通大学', '师范学校', '外国语学校', '职业学院', '佛学院', '农学院', '医学院',
                 '商学院', '工学院', '技术学院', '林学院', '理学院', '工程学院', '教育学院', '师范学院', '培训学院', '学院', '军校', }},

    # 协会委会
    '协会': {'.': {types.NM, types.org}, '-': {},
           '+': {'企业协会', '行业协会', '服务协会', '警察协会', '老年协会', '技术协会', '科学技术协会', '职工技术协会', '管理协会', '交流协', '教育学会', '图书馆学会', '总会',
                 '志愿者协会', '用水者协会', '体育协会', '计划生育协会', '校友会', '商会', '学会', '研究会', '联谊会', '促进会', '体协', '技协', '消协', '职工技协', "持股会", "职工持股会",
                 }, '-': {'协助', '协调'}},
    '联合会': {'.': {types.NM, types.org}, '-': {},
            '+': {'商业联合会', '工商业联合会', '残疾人联合会', '妇女联合会', '残联', '妇联', '文联', '社科联'}},
    '委员会': {'.': {types.NM, types.org}, '-': {},
            '+': {'工会委员会', '工作委员会', '村民委员会', '管理委员会', '居委会', '常委会', '人大常委会', '村委会', '管委会', '组委会', '委会', '区委', '县委', '村委', '纪委',
                  '工作委', '常务委', '居民委', '村民委', '政法委', '管理委', '党委', '卫健委', '发改委', '州委', '工会委', '工委', '建委', '教委', '文化委', '文卫委', '旅发委',
                  '纪工委', '纪检委', '经贸工委', '计生委'}},
    '十字会': {'.': {types.NM, types.org, types.medical}, '-': {},
            '+': {'红十字会', '红十会'}},
    '工会': {'.': {types.NM, types.org, types.gov}, '-': {},
           '+': {'机关工会', '分工会', '总工会', '教育工会', "工会小组", }},
    # 金融机构
    '基金会': {'.': {types.NM, types.financial},
            '+': {'互助资金', '基金', '发展基金会', '教育基金会', '产业基金', '发展基金', '投资基金'}, '-': {'基金管理', '基金投资'}},
    '股权投资': {'.': {types.NM, types.financial},
             '+': {}, '-': {'资产管理', '投资管理'}},
    '信用社': {'.': {types.NM, types.financial}, '-': {},
            '+': {'信用联社', '农村信用联社', }},
    '银行': {'.': {types.NM, types.financial}, '-': {'行走', '行为'},
           '+': {'储蓄所', '分行', '支行', '总行', '商业银行', '农村商业银行', '农村合作银行', '工商银行', '邮政储蓄银行', '村镇银行', '开发区支行', '小微支行'}},
    # 供销合作
    '服务社': {'.': {types.NM, types.service}, '-': {},
            '+': {'会社', '军人服务社', '综合服务社', '互助社', '代办', '电信代办', '业务代办', '服务所', '科技社', "理事会", "红白理事会", "中介所", "介绍所", "职业介绍所", }},
    '合作社': {'.': {types.NM, types.industry, types.farming}, '-': {},
            '+': {'专业合作', '种植专业合作', '养殖专业合作', '合社', '综合社', '联合社', '经济联合社', '合作社联合社', '专业合作社联合社', '供销合作社联合社', '合作社联社',
                  '联社', '合作联社', '专业合作联社', '信用合作联社', '农村信用合作联社', '经济社', '合作经济社', '专业合作社', '股份合作社', '互助合作社', '经济合作社',
                  '信用合作社', '供销合作社', "合作厅", }},
    '供销社': {'.': {types.NM, types.retail}, '-': {},
            '+': {'经销社', '经营部', '经部', '销部', '营部', '配部', '经销部', '营销部', '购销部', '销售部', '零售部', '农资经营部', '营业部', '租赁站', '购销站',
                  '销售处', '分理处', '售票处', '经销处', '经销商', '供应商', '总经销'}},
    '联合体': {'.': {types.NM, types.com}, '-': {'体育', '体操'},
            '+': {'联营体', '共同体', '医共体', }},
    # 科研院所
    '研究院': {'.': {types.NM, types.tech}, '-': {},
            '+': {'科学研究院', '科技研究院', '设计研究院', '测绘院', '研究总院', '设计研究总院', '总院', '设计院', '规划设计院', '勘察设计院', '工程设计院',
                  '建筑设计院', '勘察院', '科学院', '中国科学院', '城建院', '社科院', '管理院', "规划院", "勘查院", "考试院", }},
    '研究所': {'.': {types.NM, types.tech}, '-': {},
            '+': {'设计所', '检验所', '药品检验所', '检测所', '防治所', '科学研究所', '设计研究所', '监督所', '卫生监督所'}},
    '监测台': {'.': {types.NM, types.tech}, '-': {},
            '+': {'地震台', '基准台', '天文台', '实验台', '寻呼台', '信息台', '信息台', '查询台', '气象台', '海洋预报台', '观象台', '预报台'}},

    # 医疗福利
    '福利院': {'.': {types.NM, types.service}, '-': {},
            '+': {'护理院', '敬老院', '养老院', '社会福利院', '农村福利院', '儿童福利院', '保育院', "互助会", "慈善会", "光荣院", }},
    '殡仪馆': {'.': {types.NM, types.service}, '-': {},
            '+': {'陵园', '公墓', '安息园', '火葬场', '寝园', '骨灰林', '塔陵', '安息陵', '墓区', }},

    '医院': {'.': {types.NM, types.medical}, '-': {},
           '+': {'中医院', '妇产医院', '中医医院', '康复医院', '附属医院', '职工医院', '中心医院', '总医院', '人民医院', '动物医院', '宠物医院', '精神病医院', "血站",
                 '专科医院', '眼科医院', '骨科医院', '口腔医院', '蒙医院', '藏医院', '美容院', '卫生院', '疗养院', '保健院', '妇幼保健院', '门诊', '诊所', "医务室",
                 '中医诊所', '卫生所', '美容门诊', '口腔门诊', '门诊部', '口腔门诊部', '医科', '眼科', '脑科', '卫生室', '医院新院', '中心血库', '血库', "防治院", }},
    '药店': {'.': {types.NM, types.medical, types.retail}, '-': {},
           '+': {'国药号', '药号', '药房', '大药房', '药铺', '药行', '药材行', '药材站', '药材栈', '药庄', '药妆店', '药堂', '药品部', '药品超市', '药品站',
                 '药品店', '药具站', '草药部', '草药站', '膏药老店', '老药铺', '老膏药铺', '膏药铺', '新特药部', '药部', '大药店', '大药行', '国药馆', '医药馆',
                 '医药量贩', '医药部', '医药行', '医药站', '医药店', '医药市场', '医药商店', '中药馆', '中西药行', '中药饮片部', '中药部', '中药配方部', '中药行',
                 '中药材部', '中草药馆', '中草药行', '中药铺', '药品行', '藥號'}},
    # 文化娱乐
    '影剧院': {'.': {types.NM, types.cultural}, '-': {},
            '+': {'剧院', '影院', '影都', '大剧院', '电影院', '歌剧院', '剧团', '曲剧团', '影城', '电影城', '艺术团', '乌兰牧骑', '影埸', "录像厅", "舞团", "歌舞团",
                  "乐团", "合唱团", }},
    '书画院': {'.': {types.NM, types.cultural}, '-': {},
            '+': {'书法院', '画院', '书院', '书肆', '书馆', '画廊', '书房', '书轩', '品味轩', '墨轩', '文印轩', '瓷轩', '画轩', '石轩', "书社", "美术社", '书舍', '画舍', }},
    '博物馆': {'.': {types.NM, types.cultural, types.edu}, '-': {},
            '+': {'文化馆', '科技馆', '纪念馆', '美术馆', '艺术馆', '档案馆', '图书馆', '教育馆', '体验馆', '艺馆', '科普馆', "娱乐厅", "展厅", "展览馆", }},
    '文化宫': {'.': {types.NM, types.cultural}, '-': {},
            '+': {'工人文化宫', '少年宫', '青少年宫', '体育馆', '球馆', '体育场', '溜冰埸', '旱冰场', '滑冰场', '冰球馆', '冰球场'}},
    '出版社': {'.': {types.NM, types.cultural}, '-': {},
            '+': {'杂志社', '报社', '日报社', '音像出版社'}},
    '文印社': {'.': {types.NM, types.service}, '-': {},
            '+': {'印社', '打字复印社', '打印社', '复印社', '复印店', '印务部', '复印部', '文印部', "制作室", "文印室", "文印店", "摄影店", "图文店", "印务社", "刻字社",
                  "图文社", "图片社", "快印店", "图文快印店", "打印店", '照相馆', '相馆', "像馆", "照像馆", "影楼", "印刷部", "快印部", "美术部", "工艺部", }},
    '信息港': {'.': {types.NM, types.service, types.communica}, '-': {},
            '+': {'网咖', '网络会所', '网咖店', '网吧', '数码港'}},
    '电视台': {'.': {types.NM, types.communica}, '-': {},
            '+': {'电视站', '广播电视站', '广播电视台', '广播电台', '中心台', '中波台', '交换台', '传呼台', '传输台', '传输总台', '发射台', '发射总台', '差转台',
                  '广播影视台', '广播电视总台', '录转台', '微波台', '收转台', '电台', '电视录转台', '电视总台', '电视收转台', '电视监测台', '调频台', '转播台', }},

    # 食品餐饮
    '饭店': {'.': {types.NM, types.catering}, '-': {},
           '+': {'快餐', '餐饮店', '食店', '冷饮店', '饼店', '酒楼', '大酒楼', '大饭店', '酒家', '大酒家', '食堂', '大食堂', '职工食堂', '餐厅', }},
    '茶馆': {'.': {types.NM, types.catering}, '-': {},
           '+': {'茶社', '茶庐', '茶楼', '茶舍', '茶座', '茶饮', '茶艺', '茶都', '茶莊', '茶艺居', '茶叶店', '茶居', '茶港', '茶荘', '茗茶庄', '茶庄', '茗茶轩', '茶轩',
                 "茶室", "茶坊", }},
    '家宴': {'.': {types.NM, types.catering}, '-': {'宴席', '宴会', '宴请'},
           '+': {'全猪宴', '农家宴', '渔家宴', '藏家宴', '饺子宴', '全羊宴', '博食宴', '豆腐宴', '鸽宴'}},
    '饭庄': {'.': {types.NM, types.catering}, '-': {},
           '+': {'面莊', '饭莊', '鱼莊', '羊肉府', '美食府', '食府', '美食荟', '美食都', '鱼府', '干锅居', '火锅居', '砂锅居', '美食居', '饺子居', '饭桩', "饭堂",
                 '美食林', '麻辣烫', '麻辣烫店', '粥荘', '食荘', '饭荘', '鱼荘', '面荘', '食庄', '食莊', '豆花庄', '面庄', '鱼庄', '鲜味渔庄', '渔家庄', '渔庄', '烤羊庄', '羊庄',
                 '炖鱼村', '江鱼村', '渔村', '火锅村', '烙馍村', '美食村', '莜面村', '饺子村', "餐部", "味馆", "餐饮馆", }},
    '排档': {'.': {types.NM, types.catering, types.retail}, '-': {},
           '+': {'排挡', '大排档', '大排挡', '专档', '干调档口', '档口', '面档口', '饭档口', '麻辣香锅档口'}},
    '海鲜舫': {'.': {types.NM, types.catering}, '-': {},
            '+': {'海鲜鲂', '河鲜舫', '湖鲜舫'}},
    '家常菜': {'.': {types.NM, types.catering}, '-': {},
            '+': {'私房菜', '小饭桌', '小餐桌', '小吃', '汤馆', '粉馆', '肉馆', '酒馆', '面馆', '鱼馆', '农家菜馆', '洒家', '渔家', '酒玩家', '饼家', }},
    '食品店': {'.': {types.NM, types.retail, types.catering}, '-': {},
            '+': {'新鲜屋', '甜品店', '饮品店', '汉堡店', '包子店', '水果店', '蛋糕房', '食品门市', '食品超市', '水果超市', '副食部', '餐饮部', '蛋糕店', '茶店', "包子铺", "馕店", "鱼店",
                  '粮店', '油店', '粉店', '肉店', '菜店', '面店', '鸡店', '鸭店', '副食超市', '生鲜超市', '馍房', "奶吧", "水吧", "烤吧", "饼屋", "串店", "汤店", "馒头店", "鸡排店",
                  "奶店", "冰淇淋店", "糕点店", "烘焙店", "凉皮店", "果蔬店", "水饺店", "馍店", '饮舍', "饮吧", "面包坊", "蛋糕坊", "豆腐坊", "食坊", "鸭脖店", "豆腐店", "披萨店", "米店",
                  "粥店", "火烧店", "鲜果店", "饮料店", "调料店", "点心店", "饺子店", "寿司店", "卤味店", "果品店", "小炒店", "面皮店", "砂锅店", "馄饨店", "海鲜店", "生鲜店", "面包房",
                  "甜品站", "果行", '海鲜港', }},
    '酒庄': {'.': {types.NM, types.catering}, '-': {},
           '+': {'酒都', '酒廊', '美酒荟', '红酒庄', '酒肆', '酒池', '酒荘', }},
    # 旅游住宿
    '旅行社': {'.': {types.NM, types.tourism, types.catering}, '-': {},
            '+': {'中国旅行社', '假日旅行社', '假期旅行社', '国际旅行社', }},
    '宾馆': {'.': {types.NM, types.tourism, types.catering}, '-': {},
           '+': {'商务宾馆', '旅馆', '会馆', '公馆', '酒店', '大酒店', '旅店', '招待所', '客栈', '度假村', '度假邨', '旅社', '客舍', '宾舍', '宿舍', '旅舍', '青年旅舍', }},
    '民宿': {'.': {types.NM, types.tourism}, '-': {},
           '+': {'公寓', '客莊', '山莊', '庄园', '农庄', '山庄', '大院', '居士林', '蒙古大营', '傣家园', '农家园', '幸福家园', '残疾人之家', '农家', '老年公寓',
                 '农家乐', '牧家乐', '林家乐', '农家小院', '农家庭院', '农荘', '山荘', '剑荘', '休闲庄', '农家庄', '农家饭庄', '休闲村', '儿童村', '博览村', '娱乐村', '文化村',
                 '渡假村', '温泉村', '山水庄', }},
    '寺院': {'.': {types.NM, types.relig}, '-': {},
           '+': {'洞召', '清真寺', '佛堂', '佛寺', '佛禅寺', '古寺', '圆通寺', '地藏寺', '大寺', '女寺', '宁禅寺', '少林寺', '广福寺', '普济寺', '清凉寺', '清真女寺',
                 '观音寺', '龙泉寺', '天主堂', '天主教下会点', '天主教公所', '天主教堂', '天主教活动场所', '天主教祈祷所', '教堂', '中寺'}},
    # 洗浴会所
    '浴池': {'.': {types.NM, types.service}, '-': {},
           '+': {'康浴园', '浴部', '泉浴城', '浴吧', '浴场', '浴室', '浴宫', '浴池店', '浴池部', '浴苑', '浴都', '淋浴厅', '淋浴店', '休闲池', '药池', "浴馆", }},
    '游泳池': {'.': {types.NM, types.sports}, '-': {},
            '+': {'游泳吧', '游泳场', '游泳跳水馆', '游泳馆'}},
    '会所': {'.': {types.NM, types.service}, '-': {},
           '+': {'美容会所', '养生会所', '休养所', '沙龙', '生活馆', "保健所", }},
    '俱乐部': {'.': {types.NM, types.org, types.service}, '-': {},
            '+': {'足球俱乐部', '体育俱乐部', '青少年体育俱乐部', '健身俱乐部', '部落', '棋牌室', '舞厅', '歌舞厅', '歌厅', '之家', '地带', '骑行者之家', '休闲汇',
                  '娱乐汇', '音乐汇', '渔排垂钓'}},
    '美容美体': {'.': {types.NM, types.service}, '-': {},
             '+': {'发艺', '发典', '理发店', '发厅', '发廊', '美发店', '美甲店', '美容店', '按摩店', '足浴店', '美容馆', '养生馆', '发荘', "发室", "理发室", "发屋", "发艺店",
                   "养生店", "足疗店", "造型店", '发舍', '香舍', "美体店", "保健馆", "服务馆", "健身馆", "按摩馆", "理疗馆", }},

    # 商业销售
    '商店': {'.': {types.NM, types.retail}, '-': {'店内', '市内', '市面'},
           '+': {'门店', '专门店', '专营店', '专业店', '小店', '精品店', '用品店', '日用品店', '产品店', '便利店', '加盟店', '旗舰店', '总店', '销售店', "代理店", "专属代理店",
                 '零售店', '货店', '经销店', '直营店', '经营店', '妆品店', '化妆品店', '批发店', '卖店', '特产店', '小卖店', '书店', '新华书店', '门市', '综合门市', "双代店",
                 '用品门市', '销售门市', '器材门市', '建材门市', '通讯门市', '百货门市', '收购门市', '生资门市', '超市', '平价超市', '便利超市', '用品超市', "精品屋", "专店",
                 '小超市', '便民超市', '生活超市', '百货超市', '烟酒超市', '连锁超市', '书屋', '通讯店', '农资店', '电脑店', "收购店", "代销店", "分销店", "直销店", "门业店",
                 '五金店', '金店', '花店', '便民店', '器材店', '建材店', '眼镜店', '装饰店', '手机店', '材料店', '科技店', '电器店', '加工店', '艺品店', "花坊",
                 '维修店', '配件店', '文具店', '玩具店', '服务店', '广告店', '饰品店', '超市店', '中心店', '包店', '锁店', '鞋店', '士多', '士多店', '花苑',
                 '批零部', '门窗店', '内衣店', '女装店', '童装店', '服饰店', '中学店', '万达店', "网店", "小学店", "小区店", "国际店", "体验店", "小卖铺", "补胎店", "花艺店",
                 "制衣店", "寿衣店", "表店", "电讯店", "租赁店", "电动车店", "不锈钢店", "首饰店", "护肤品店", "玉器店", "花圈店", "美妆店", "孕婴店", "装修店", "保健店", "工具店",
                 "洁具店", "皮具店", "杂品店", "阳光店", "布店", "婚庆店", "推拿店", "涂料店", "水暖店", "烟杂店", "耗材店", "钢材店", "水泥店", "卫浴店", "煤店", "宠物店",
                 "家电店", "理疗店", "瓷砖店", "护肤店", }},
    '商贸行': {'.': {types.NM, types.retail}, '-': {},
            '+': {'寄卖行', '拍卖行', '电器行', '典当行', '贸易行', '电脑行', '通讯行', '租赁行', '装饰行', '批发行', '量贩', '加油港', '汽车港', '鲜花港', "道馆", "家居馆", }},
    '商贸城': {'.': {types.NM, types.retail}, '-': {'城市', '城区'},
            '+': {'娱乐城', '家具城', '电器城', '不夜城', '电子城', '生态城', '科技城', '家电城', '家私城', '电脑城', '汽车城', '美食城', '装饰城', '自行车城', "家俱城", "鞋城", }},
    '商场': {'.': {types.NM, types.retail}, '-': {},
           '+': {'服务都', '银都', '书城', '商城', '卖场', '商都', '购物广场', '小世界', '大世界', '商厦', '商业大厦', '商埸', "展场", "家具广场", }},
    '市场': {'.': {types.NM, types.retail}, '-': {},
           '+': {'批发市场', '综合市场', '交易市场', '菜市场', '农贸市场', '大市场', '商业大都市', '花鸟鱼市', '市埸', }},
    '百货': {'.': {types.NM, types.retail}, '-': {'家居用品'},
           '+': {'百货店', '百货商店', '百货商场', '百货大楼', '总代理', '家居卖场', '家居名品馆', '家居广场', '家居形象店', }},
    '连锁': {'.': {types.NM, types.retail}, '-': {'连锁经营'},
           '+': {'农资连锁', '服务连锁', '母婴连锁', '连锁店', '连锁机构'}},
    '用品世界': {'.': {types.NM, types.retail}, '-': {},
             '+': {'化妆品世界', '女人世界', '娱乐世界', '家具世界', '文化世界', '欢乐世界', '水上世界', '游乐世界', '溜冰世界', '玩具世界', '男仕世界', '礼品世界', '箱包世界',
                   '精品世界', '花卉世界', '茶叶世界', '音像世界', '食品世界', '饰界', '乒乓世界', '魅力世界'}},
    "商亭": {'.': {types.NM, types.retail}, '-': {},
           '+': {"服务亭"}},
    '商号': {'.': {types.NM, types.retail}, '-': {'号角', '号手', '号声'},
           '+': {'南货号', '山茶号', '自行车号', '仓买', '鞋荘', "商社", }},
    '商行': {'.': {types.NM, types.retail}, '-': {},
           '+': {'琴行', '茶行', '车行', '酒行', '金行', '总汇', '傢俬', '家俬', '木雕世家', '名酒汇', '美食汇', '大全', "烟店", "玻璃店", "陶瓷店", "数码店", "家私店",
                 "烟花爆竹店", "纺店", "家纺店", "裁缝店", "商贸店", "汽配店", "轮胎店", "时装店", "男装店", "设计店", "水产店", "文体店", "制作店", "通信店", "汽修店",
                 "家俱店", "厨具店", "渔具店", "灯具店", "日化店", "灯饰店", "花卉店", "综合店", "保健品店", "制品店", "礼品店", "设备店", "母婴店", "家居店", "珠宝店", "南杂店",
                 "石材店", "水洗店", "漆店", "装潢店", '花舍', '衣舍', "修理行", "眼镜行", "鞋行", "维修行", "珠宝行", "布行", "建材行", }},
    '柜台': {'.': {types.NM, types.retail}, '-': {'柜子'},
           '+': {'专柜', '代办柜', '业务柜', '服务柜', '专卖柜', '药柜', '副食柜', '肉食柜', '服饰柜', '烟柜'}},
    '摊床': {'.': {types.NM, types.individual}, '-': {},
           '+': {'干调床', '摊位', "肉摊", "肉档", "菜摊", "蔬菜摊", "菜档", "粥铺", "肉铺", }},
    # 邮政
    '邮局': {'.': {types.NM, types.postal}, '-': {},
           '+': {'邮政一站通', '邮政所', '邮政局', '邮政支局', '电信局', '电报局', '驿站', '邮政港', '驿栈'}},
    '报刊亭': {'.': {types.NM, types.retail}, '-': {'亭子'},
            '+': {'报亭', "电话亭", }},
    # 交通运输仓储
    '车务段': {'.': {types.NM, types.traffic}, '-': {'段落'},
            '+': {'房产段', '通信段', '大修段', '检修段', '维修段', '分段', '工务段', '服务段', '机务段', '电务段', '综合段', '房建公寓段', '施工段', '桥工段', '供应段', '房建段',
                  '养护段', '材料段', '基础设施段', '工务机械段', '供水段', '生活段', '轮渡段', '管理段', '公路管理段', '运用段', '供电段', '工电段', '水电段', '工程段', '建筑段',
                  '技能训练段', '多种经营段', '公路段', '养路段', '动车段', '客车段', '焊轨段', '机辆段', '车辆段', '铁路运输段', '客运段', '航道段', '修防段', '总段', '维管段', }},
    '码头': {'.': {types.NM, types.traffic}, '-': {},
           '+': {'渡口', '港口', '航空港', '港湾', '机场', '国际机场', '客运主枢纽', '航电枢纽', '重件码头', '服务码头', '装卸码头', '渔港监督', '粮港', '联运港', '货运港', }},
    '车站': {'.': {types.NM, types.traffic}, '-': {},
           '+': {'汽车站', '火车站', '东站', '北站', '南站', '西站', '中心站', '总站', '客运站', '汽车客运站', '铁路专用线', "货站", '站台', '配送平台', '枢纽台', '发运站台',
                 "中转站", "运输站", "储运站", "货运站", "转运站", "收费站", "配送站", "收储站", }},
    '货运部': {'.': {types.NM, types.traffic}, '-': {},
            '+': {'物资部', '汽车部', '运输部', '配送部', '发行部', '汽车队', '运输队', '运输户', '轿车运输', '货车运输', '机修班', '汽车班', '运输班', "托运部", "物流部", }},
    '仓库': {'.': {types.NM, types.logistics}, '-': {'库内', '库存', '库中'},
           '+': {'储备库', '粮食储备库', '直属库', '粮库', '仓储', '粮站', '货仓', '资料仓', '配送仓', '供应仓', '保税仓', '保管仓', '前置仓', '副食仓', '化肥仓', '工艺仓', '布仓',
                 '批发仓', '批发货仓', '物资仓', '盐仓', '监管仓', '粮仓', '肥料仓', '中心库', '(配送)库', '中转库', '仓储库', '供应总库', '保税库', '保鲜库', '储备库', '储藏库',
                 '冷库', '冷藏库', '冻库', '分库', '化肥库', '器材库', '购销库', '寄售库', '总库', '恒温库', '收储库', '收纳库', '果品库', '气瓶库', '沥青库', '油库', '油脂库', '物资库',
                 '储运库', '直管库', '石油气库', '糖库', '装备库', '配送库', '仓储栈', '储运栈', '转运栈', '煤栈', '煤炭仓储栈', '货栈', '贸易栈', '贸易货栈', '暖车库', '车库'}},

    # 园区
    '游乐园': {'.': {types.NM, types.cultural}, '-': {},
            '+': {'乐园', '公园', '游乐场', '森林公园', '动物园', '风景园', '娱乐湾'}},
    '产业园': {'.': {types.NM, types.industry, types.service}, '-': {},
            '+': {'科技产业园', '创业园', '工业园', '软件园', '科技园', '创新园', '示范园', '物流园', '发展园'}},
    '园区': {'.': {types.NM, types.service, types.industry}, '-': {},
           '+': {'度假区', '旅游度假区', '服务区', '产业园区', '物流园区', '景区', '旅游景区', '片区', '管理区', '社区', '示范区', '作业区', '停车区', '库区', '教区', '旅游区',
                 '旅游渡假区', '渡假区', '游览区', '物业区', '示范小区', '管护区', '联合小区', '采区', '院区'}},

    # 局所处
    '事务局': {'.': {types.NM, types.gov}, '-': {},
            '+': {'农业局', '林业局', '电业局', '工作局', '商务局', '水利局', '规划局', '城乡规划局', '信息化局', '矿务局', '水务局', '服务局', '就业服务局', '环境局',
                  '生态环境局', '招商局', '开发局', '草原局', '林业和草原局', '兽医局', '畜牧兽医局', '发展局', '经济发展局', '健康局', '卫生健康局', '保障局', '社会保障局',
                  '地震局', '粮食局', '改革局', '发展和改革局', '运输局', '交通运输局', '促进局', '交通局', '干部局', '老干部局', '信访局', '气象局', '铁路局', '公路局',
                  '教育局', '计划生育局', '机要局', '电视局', '广播电视局', '统计局', '建设局', '城乡建设局', '规划建设局', '税务局', '国家税务局', '地方税务局', '工程局', '体育局',
                  '教育和体育局', '档案局', '出版局', '新闻出版局', '检疫局', '检验检疫局', "事业局", "海事局", "水产局", "物价局", "合作局", "振兴局", "乡村振兴局",
                  "储备局", "移民局", "广电局", "保险局", }},
    '管理局': {'.': {types.NM, types.gov}, '-': {},
            '+': {'事务管理局', '城市管理局', '应急管理局', '石油管理局', '监督管理局', '工程管理局', '建设管理局', '公路管理局', '运输管理局', '财政局', '民政局', '科学技术局',
                  '总局', '审批局', '行政审批局', '环境保护局', '科技局', '保护局', '环保局', '农村局', '农业农村局', '资源局', '国土资源局', '卫生局', '旅游局', '综合执法局',
                  '行政执法局', '执法局', '稽查局', '监督局', "管局", "监管局", "就业局", "渔业局", "海洋与渔业局", "通信局", "河务局", "保密局", "机要保密局", "水土保持局", "知识产权局",
                  "园林局", "勘测局", "能源局", "农牧局", "畜牧局", "文物局", }},
    '管理所': {'.': {types.NM, types.gov}, '-': {},
            '+': {'资源管理所', '工程管理所', '建设管理所', '公路管理所', '运输管理所', '交通管理所', '保管所', '城管所', '房管所', '托管所', '水管所', '监管所', '粮管所',
                  '运管所', '管所', '中心所', '财政所', '资源所', '国土资源所', '自然资源所', "干休所", "电信所", "水利所", "税务所", "环卫所", "工商所", "国土所", "保护所",
                  "民政所", "执法所", "邮电所", "科研所", "财税所", "粮所", "测绘所", "教育所", "收费所", }},
    '管理处': {'.': {types.NM, types.gov}, '-': {},
            '+': {'物业管理处', '园林管理处', '工程管理处', '建设管理处', '公路管理处', "秘书处", "海事处", "筹建处", }},
    '服务处': {'.': {types.NM, types.gov}, '-': {},
            '+': {'工程处', '建筑工程处', '安装工程处', '联络处', '经营处', '代表处', '登记处', '婚姻登记处', '公证处', "报名处", "施工处", "供应处", "接待处", "维修处", "代售处", "代理处",
                  "安装处", "租赁处", "分销处", "购销处", }},
    '专业署': {'.': {types.NM, types.gov}, '-': {},
            '+': {'住房保障署', '促进署', '保障署', '公平贸易促进署', '出版总署', '分署', '城市景观管理署', '城市管理署', '审计署', '建筑工务署', '开发建设署', '开发署',
                  '投资推广署', '服务署', '水务署', '物流服务署', '管理署', '行政公署', '责任审计专业署'}},
    '营业所': {'.': {types.NM, types.service, types.tech}, '-': {},
            '+': {'事务所', '律师事务所', '工程师事务所', '会计师事务所', '交易所', '产权交易所', "营业处", "售楼处", "直销处", "保障所", "规划所", "监理所", "测试所", }},
    # 服务厅站
    '管理站': {'.': {types.NM, types.gov}, '-': {},
            '+': {'管理总站', '检查站', '边防检查站', '植检站', '植保植检站', '检测站', '监测站', '环境监测站', '水利管理站', '救助管理站', '监督管理站', '工程管理站', '建设管理站',
                  '公路管理站', '检疫站', '监督站', '质量监督站', '服务股', '管理股', '工程股', }},
    '供应站': {'.': {types.NM, types.service}, '-': {},
            '+': {'食品站', '推广站', '技术推广站', '液化气供应站', '军粮供应站', '采购供应站', '物资供应站', '技术推广总站', '气站', '液化气站', }},
    '服务站': {'.': {types.NM, types.retail}, '-': {},
            '+': {'工作站', '维修站', '汽车维修站', '劳动服务站', '社区服务站', '文化站', "批发站", "防疫站", "安监站", "统计站", "建设站", "采购站", "物资站", "试验站",
                  "指导站", "保护站", "搅拌站", "防治站", "监理站", "经营站", "经销站", "检验站", "军供站", "保健站", "妇幼保健站", "救助站", "供热站", "修理站", "护理站",
                  "仪器站", "接待站", "水土保持站", "交流站", }},
    '营业厅': {'.': {types.NM, types.retail}, '-': {},
            '+': {'服务厅', '咖啡厅', '展示厅', '营业班', '营销班', }},

    # 业务部门
    '技术部': {'.': {types.NM, types.tech}, '-': {},
            '+': {'工程部', '装饰工程部', '安装部', '设计部', '培训部', '通讯部', '咨询部', '开发部', }},
    '服务部': {'.': {types.NM, types.service}, '-': {},
            '+': {'维修服务部', '技术服务部', '咨询服务部', '广告部', '摄影部', '信息部', '服务房', "生产部", "装修部", "策划部", "综合部", "商品部", "发展部", "材料部", "器材部", "电焊部",
                  "电脑部", "编辑部", }},
    '管理部': {'.': {types.NM, types.gov}, '-': {},
            '+': {'宣传部', '武装部', '监理部', '经理部', '组织部', '水利部', '统战部', '科技部', '指挥部', }},
    '修理部': {'.': {types.NM, types.service}, '-': {},
            '+': {'维修部', '电器维修部', '家电维修部', '汽车维修部', '汽车修理部', '汽修部', }},
    '供应部': {'.': {types.NM, types.retail}, '-': {},
            '+': {'收购部', '商贸部', '租赁部', '生资部', '贸易部', '售楼部', }},
    '业务部': {'.': {types.NM, types.com}, '-': {},
            '+': {'事业部', '代理部', }},
    '加工部': {'.': {types.NM, types.industry}, '-': {},
            '+': {'制作部', '装潢部', '装璜部', '建材部', '配件部', '装饰部', '广告装饰部', '工作部'}},
    '工作室': {'.': {types.NM, types.tech}, '-': {},
            '+': {'制作工作室', '设计工作室', '实验室', '设计室', '设计窒', '婚典'}},

    # 业务科室队
    '业务科': {'.': {types.NM, types.gov}, '-': {},
            '+': {'农业科', '文化科', '装备科', '器械科', '机械科', '检测科', '交通科', '基建连', '基建处', '基建科', "督导室", "教研室", "督查室", "档案室", "试验室", }},
    '管理大队': {'.': {types.NM, types.gov}, '-': {},
             '+': {'救援队', '消防队', '稽查队', '调查队', '执法队', }},
    '服务队': {'.': {types.NM, types.service}, '-': {},
            '+': {'维修队', '劳务队', '装卸队', '施工队', '工程队', '土石方工程队', '建筑工程队', '建筑队', '测绘队', '修缮队', '安装队', '设计队', '养护队', '城调队',
                  '救护队', "专业队", "工作队", "绿化队", "监察队", "搬运队", "测量队", }},
    '服务点': {'.': {types.NM, types.service}, '-': {},
            '+': {'代办点', '代售点', '销售点', '零售点', '供应点', '网点', '收购点', '护林哨', '机动车检测线', '收购线', '检测线', '服务窗口', "营业点", "加工点",
                  "代理点", "配送点", "代销点", "直销点", "经销点", "活动室", "游戏室", "招生点", "经营点", "报名点", "教学点", "库点", "供气点", "加油点", }},
    '业务股': {'.': {types.NM, types.gov}, '-': {'股票', '股份'},
            '+': {'优抚股', '住宅与房地产股', '体卫安全股', '保障股', '信访股', '储运股', '公路股', '农业农经股', '农机股', '医政医管股', '基本建设股', '基础教育股',
                  '山林特产股', '成教股', '执法监督股', '推广教育股', '教育股', '林业公安股', '林政股', '水政水资源股', '法规股', '电教股', '社政股', '经销股', '综合股',
                  '耕地保护利用股', '能源统计股', '营林股', '规划与水利股', '规划股', '造林股', '预算股'}},

    # 农牧业
    '鱼塘': {'.': {types.NM, types.fishery}, '-': {},
           '+': {'渔塘', '鱼池', '渔港', '养殖基池', '基池', '养鱼池', '鱼池', '养鱼塘', "渔场", "鱼场", }},
    '种植场': {'.': {types.NM, types.farming}, '-': {},
            '+': {'花圃', '苗圃', '桃园', '梨园', '茶园', '菜园', '果园', '园艺', '大棚', '种植园', '农场', '木场', '林场', '果场', '苗场', '茶场', '菜场', '花木场',
                  '苗木基地', '种植基地', '植物园', '花园', '苗圃场', '花木园', '山林场', '国有林场', '园艺场', '绿化园', '农业园', '花卉园', '生态园', '大棚', '温室大棚',
                  '蔬菜温室大棚', '养殖地', '橡胶地', '种植地', '总埸', '林埸', '垦区', '种植示范小区', '营林区', "发展场", "农林发展场", "农业发展场", "蔬菜发展场", }},
    '养殖场': {'.': {types.NM, types.breeding}, '-': {},
            '+': {'猪场', '羊场', '马场', '鸡场', '养殖基地', '水产养殖场', '猪养殖场', '生猪养殖场', '垦殖场', '牧场', '原种场', '良种场', '养殖埸', '养殖总埸', '养殖总场',
                  '养殖小区', '养猪小区', '牧业小区', '养殖舍', '犬舍', '猫舍', '鸡舍', '鸽舍', "种养场", "饲养场", "繁育场", "畜牧发展场", "肉牛发展场", "养殖发展场", }},
    '肥药站': {'.': {types.NM, types.farming, types.retail}, '-': {},
            '+': {'肥药部', '农药店', '农药部', '农药门市', '兽药部', '兽药行', '兽药店', '农药站', '兽药站', '农药铺', "农家店", "种子店", "化肥店", "购销店", "谷店",
                  "土肥站", "种苗站", "烟草站", "烟站", "烟叶站", "植保站", '林业站', '林业工作站', "农技站", "水产站", "种子站", "茧站", '兽医站', '畜牧兽医站', "农资部",
                  }},
    '水库': {'.': {types.NM, types.irrigation}, '-': {},
           '+': {'水站', '翻水站', '扬水站', '供水站', '水利站', "水务站", }},

    # 高频单字尾缀
    '厂': {'.': {types.NO, types.industry}, '-': {'厂房', '厂区', '厂长', '厂内', '厂外', '间距', '间隔'},
          '+': {'车间'}},
    '城': {'.': {types.NO}, '-': {'城墙', '城门'},
          '+': {}},
    '部': {'.': {types.NO}, '-': {'部门', '部长', '部分'},
          '+': {'总部'}},
    '馆': {'.': {types.NO, types.service}, '-': {'馆长', '馆藏'},
          '+': {}},
    '所': {'.': {types.NO}, '-': {'所长', '所以', '所得'},
          '+': {}},
    '局': {'.': {types.NO, types.gov}, '-': {'局长', '局部', '局座', '局域'},
          '+': {'(体育)局', '(侨务)局', '(农林水利)局', '(文化)局', '(新闻出版)局', '(水务)局', '(版权)局', '(综合执法)局', '(综合行政执法)局', '(质量技术监督)局'}},
    '厅': {'.': {types.NO}, '-': {'厅长'},
          '+': {}},
    '行': {'.': {types.NO}, '-': {'行长'},
          '+': {}},
    '团': {'.': {types.NO}, '-': {'团长', '团员', '团结'},
          '+': {'生产建设兵团', }},
    '房': {'.': {types.NO}, '-': {'房子', '房间', '房屋', '房内'},
          '+': {}},
    '堂': {'.': {types.NO}, '-': {'堂堂'},
          '+': {}},
    '宫': {'.': {types.NO}, '-': {'宫殿'},
          '+': {}},
    '队': {'.': {types.NO}, '-': {'队长'},
          '+': {'中队', '井队', '大队', '总队', '支队', '车队'}},
    '社': {'.': {types.NO}, '-': {'社长'},
          '+': {'总社', }},
    '阁': {'.': {types.NO}, '-': {'阁楼'},
          '+': {}},
    '坊': {'.': {types.NO}, '-': {'坊间', '街坊'},
          '+': {}},
    '楼': {'.': {types.NO}, '-': {'楼房', '楼宇', '楼层', '楼间距', '楼内', '楼外', '楼上', '楼下', '楼中', '楼里'},
          '+': {}},
    '院': {'.': {types.NO}, '-': {'院长', '院方', '院子', '院部'},
          '+': {}},
    '轩': {'.': {types.NO}, '-': {}, '+': {}},
    '斋': {'.': {types.NO}, '-': {}, '+': {}},
    '矿': {'.': {types.NO}, '-': {}, '+': {}},
    '苑': {'.': {types.NO}, '-': {}, '+': {}},
    '亭': {'.': {types.NO}, '-': {}, '+': {}},
    '科': {'.': {types.NO}, '-': {}, '+': {}},
    '摊': {'.': {types.NO}, '-': {}, '+': {}},
    '档': {'.': {types.NO}, '-': {}, '+': {}},
    '会': {'.': {types.NO}, '-': {}, '+': {'(协)会'}},
    '办': {'.': {types.NO}, '-': {}, '+': {}},
    '屋': {'.': {types.NO}, '-': {}, '+': {}},
    '组': {'.': {types.NO}, '-': {}, '+': {}},
    '吧': {'.': {types.NO}, '-': {}, '+': {}},
    '铺': {'.': {types.NO}, '-': {}, '+': {}},
    '园': {'.': {types.NO}, '-': {}, '+': {}},
    '点': {'.': {types.NO}, '-': {}, '+': {}},
    '室': {'.': {types.NO}, '-': {}, '+': {}},
    '处': {'.': {types.NO, types.gov}, '-': {}, '+': {}},
    '场': {'.': {types.NO, types.farming}, '-': {}, '+': {}},
    '站': {'.': {types.NO, types.service}, '-': {}, '+': {}},
    '店': {'.': {types.NO, types.retail}, '-': {}, '+': {}},

    # 后置冠字
    '(协会)': {'.': {types.NL, types.org}, '-': {},
             '+': {'(商会)', '(总商会)'}},
    '(托养中心)': {'.': {types.NL, types.service}, '-': {},
               '+': {}},
    '(普通合伙)': {'.': {types.NL, types.financial}, '-': {},
               '+': {'(特殊合伙)', '(有限合伙)'}},
    '(有限公司)': {'.': {types.NL, types.com}, '-': {},
               '+': {'(有限责任)', '(有限责任公司)'}},

    # 前导冠字
    '中国': {'.': {types.NF, types.NS}, '-': {},
           '+': {'中华人民共和国'}},
    '中共': {'.': {types.NF, types.gov}, '-': {},
           '+': {'中国共产党','共产党'}},
    '中铁': {'.': {types.NF, types.com}, '-': {},
           '+': {'中交', '中建', '国网', '国电', '中烟', '中电', '中电建', '国家税务总局', '华能', '华电', '华润'}},

}


def make_tails_data():
    """利用内置NT组份表构造直观映射表"""
    rst = {}
    for tn in nt_tails:
        typs = deepcopy(nt_tails[tn]['.'])
        exts = nt_tails[tn]['+']
        if types.NO not in typs:
            rst[tn] = typs
        else:
            typs.remove(types.NO)
        for en in exts:
            assert en not in rst, en
            rst[en] = typs
    return rst


# 生成tail组份映射表
nt_tail_datas = make_tails_data()


def query_tail_data(tail, with_NO=True):
    """查询指定的尾缀tail对应的组份类型信息.返回值:None或set(组份类型)"""
    if len(tail) == 1 and with_NO:
        return nt_tails.get(tail, None)
    return nt_tail_datas.get(tail, None)
