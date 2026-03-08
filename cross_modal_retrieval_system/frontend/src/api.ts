import type { ProductDisplayItem, RetrievalItem, RetrievalResponse } from "./types";

type MockProduct = {
  product_id: number;
  title: string;
  description: string;
  image_url: string;
  industry: string;
  cate1: string;
  cate2: string;
  cate3: string;
  cate4: string;
  price: string;
};

const MOCK_PRODUCTS: MockProduct[] = [
  {
    product_id: 1001,
    title: "cob防眩射灯客厅家用射灯嵌入式小山丘射灯洗墙灯无主灯设计照明",
    description: "家装 | 灯具光源 | 无主灯类灯饰 | 嵌入式射灯 | 功能功效:防眩",
    image_url: "https://img.alicdn.com/imgextra/i1/2214208291760/O1CN01HbliL11Os7u3pHquA_!!2214208291760.jpg",
    industry: "家装",
    cate1: "灯具光源",
    cate2: "无主灯类灯饰",
    cate3: "无主灯类灯饰",
    cate4: "嵌入式射灯",
    price: "¥129.00"
  },
  {
    product_id: 1002,
    title: "Fion/菲安妮菜篮子水桶子母包 2022新款女包时尚高级感单肩斜挎包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 品类:女包/斜挎包",
    image_url: "https://img.alicdn.com/imgextra/i2/2211390316408/O1CN01VLl19A1xCunwteozo_!!2211390316408.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥269.00"
  },
  {
    product_id: 1003,
    title: "香港代购轻奢品牌包包2023新款手提帆布格纹水桶包大容量斜挎女包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 水桶包 | 材质:帆布",
    image_url: "https://img.alicdn.com/imgextra/i1/1946161543/O1CN01GPqPil1NGjv5PUlv9_!!1946161543.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "水桶包",
    price: "¥238.00"
  },
  {
    product_id: 1004,
    title: "2023春秋季新款恒源祥夹克中年男休闲高端桑蚕丝公务员免烫薄外套",
    description: "服饰时尚 | 男装 | 夹克 | 春秋季 | 桑蚕丝 | 中年男",
    image_url: "https://img.alicdn.com/imgextra/i3/682420287/O1CN01ORwXVn1DzUTxo3Dlg_!!682420287.jpg",
    industry: "服饰时尚",
    cate1: "男装",
    cate2: "夹克",
    cate3: "夹克",
    cate4: "夹克",
    price: "¥359.00"
  },
  {
    product_id: 1005,
    title: "钓鱼台 大师级/丰顺/黑金/雅赏/天地人和/七星芳华/珐琅彩 整箱装",
    description: "食品生鲜 | 美酒 | 国产白酒 | 白酒/调香白酒 | 黑金",
    image_url: "https://img.alicdn.com/imgextra/i1/2215034250644/O1CN01eQD8wd1GcztdhqJZW_!!2215034250644.jpg",
    industry: "食品生鲜",
    cate1: "美酒",
    cate2: "国产白酒",
    cate3: "国产白酒",
    cate4: "白酒/调香白酒",
    price: "¥899.00"
  },
  {
    product_id: 1006,
    title: "2023春季新款MM6德训小白鞋女情侣系带真皮休闲运动饼干厚底鞋",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 时装单鞋 | 松糕鞋 | 真皮",
    image_url: "https://img.alicdn.com/imgextra/i2/2209538759222/O1CN01zcuKes2HzjKfRS4ws_!!2209538759222.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "时装单鞋",
    cate4: "松糕（摇摇）鞋",
    price: "¥189.00"
  },
  {
    product_id: 1007,
    title: "Huawei/华为 MATE 30 5G官方旗舰原装正品mate30pro鸿蒙智能手机",
    description: "3C数码 | 手机 | 手机 | 手机 | 品牌:华为 | 型号:Mate 30 Pro",
    image_url: "https://img.alicdn.com/imgextra/i1/3051991189/O1CN01V6JqvO1KebkWkVyfv_!!3051991189.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥1999.00"
  },
  {
    product_id: 1008,
    title: "男鞋2023新款夏季透气丑萌大头休闲板鞋百搭帆布潮鞋运动小白鞋男",
    description: "服饰时尚 | 男女鞋 | 男鞋 | 休闲鞋 | 休闲板鞋 | 透气/运动",
    image_url: "https://img.alicdn.com/imgextra/i4/2208213267192/O1CN01iFXv9M22zzK30xMJw_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "男鞋",
    cate3: "休闲鞋",
    cate4: "休闲板鞋",
    price: "¥159.00"
  },
  {
    product_id: 1009,
    title: "春夏休闲速干防晒宽檐棒球帽出游快干帽子青年圆顶帽那女通用户外",
    description: "服饰时尚 | 箱包服配 | 服配 | 帽子 | 防晒户外",
    image_url: "https://img.alicdn.com/imgextra/i3/66558658/O1CN01hQ0Itg2DpPski6ykE_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "服配",
    cate3: "帽子",
    cate4: "帽子",
    price: "¥49.00"
  },
  {
    product_id: 1010,
    title: "网红主播白色蜜桃臀打底裤女薄款低腰弹力紧身显瘦翘臀健身小脚裤",
    description: "服饰时尚 | 女装 | 女士裤装 | 裤子 | 打底裤 | 弹力显瘦",
    image_url: "https://img.alicdn.com/imgextra/i2/2116409237/O1CN01Cu5LEQ2I6bAMP34NU_!!2116409237.jpg",
    industry: "服饰时尚",
    cate1: "女装",
    cate2: "女士裤装",
    cate3: "裤子",
    cate4: "打底裤",
    price: "¥79.00"
  },
  {
    product_id: 1011,
    title: "花花公子马甲背心男士含羊毛针织衫秋冬鸡心v领毛衣中年爸爸坎肩",
    description: "服饰时尚 | 男装 | 常规马甲 | 秋冬 | 羊毛 | 中年男士",
    image_url: "https://img.alicdn.com/imgextra/i4/2205735448/O1CN01vCgG4L1q7ETFGDhtQ_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男装",
    cate2: "常规马甲",
    cate3: "常规马甲",
    cate4: "常规马甲",
    price: "¥149.00"
  },
  {
    product_id: 1012,
    title: "子路潮品 欧美风新款纯欲风修身性感大方领弧形下摆长袖T恤上衣女",
    description: "服饰时尚 | 女装 | 女士T恤 | T恤 | 欧美风/修身",
    image_url: "https://img.alicdn.com/imgextra/i1/2206746970076/O1CN019xTwyW1CQqqYI7MV3_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "女装",
    cate2: "女士T恤",
    cate3: "T恤",
    cate4: "T恤",
    price: "¥119.00"
  },
  {
    product_id: 1013,
    title: "袜子女士春夏潮袜网红字母弹力水晶丝空调黑白色系中高筒薄款女袜",
    description: "服饰时尚 | 内衣 | 袜类 | 中筒袜 | 春夏弹力",
    image_url: "https://img.alicdn.com/imgextra/i3/2215302213772/O1CN01iX5sxX1djcmpV8ATg_!!2215302213772.jpg",
    industry: "服饰时尚",
    cate1: "内衣",
    cate2: "袜类",
    cate3: "袜类",
    cate4: "中筒袜",
    price: "¥29.90"
  },
  {
    product_id: 1014,
    title: "轻奢羊皮真皮手机斜挎手拿包小香风链条菱格单肩包小包宴会潮钱包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 钱包 | 羊皮真皮",
    image_url: "https://img.alicdn.com/imgextra/i2/796490729/O1CN01JE6KhL1HFvRup0Mfh_!!796490729.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "钱包",
    price: "¥319.00"
  },
  {
    product_id: 1015,
    title: "卡拉羊【推荐150cm以上】中学生立体方包男女减负防下坠书包新款",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 双肩背包 | 书包",
    image_url: "https://img.alicdn.com/imgextra/i3/4014297764/O1CN01Hdpciv27DxsROGNFf_!!4014297764.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "双肩背包",
    price: "¥169.00"
  },
  {
    product_id: 1016,
    title: "出口外贸韩国尾单撤柜女包牛皮一代爆款凯莉包经典气质单肩斜跨包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 牛皮",
    image_url: "https://img.alicdn.com/imgextra/i4/2200606695441/O1CN01sGPoFY1q41n0oZkmP_!!2200606695441.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥459.00"
  },
  {
    product_id: 1017,
    title: "双肩包女包2023新款韩版潮PU皮包女士蝴蝶结子母背包菱格纹休闲包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 双肩背包 | 韩版",
    image_url: "https://img.alicdn.com/imgextra/i2/378797279/O1CN01XATm5123dpdu7j3Ov_!!378797279.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "双肩背包",
    price: "¥229.00"
  },
  {
    product_id: 1018,
    title: "2022新款女包斜挎女包网红女包2623潮流女包休闲包包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 潮流休闲",
    image_url: "https://img.alicdn.com/imgextra/i2/702921909/O1CN01sGOQ2R1PyMr1jMgf8_!!702921909.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥139.00"
  },
  {
    product_id: 1019,
    title: "现货 香奈儿chanel 23p粉拼蓝毛呢mini cf口盖包翻盖包链条包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 香奈儿",
    image_url: "https://img.alicdn.com/imgextra/i4/374064937/O1CN01I4Rdo21mLCBUb4BSu_!!374064937.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥1280.00"
  },
  {
    product_id: 1020,
    title: "牛津布双肩包女尼龙旅行旅游背包女士休闲帆布学生书包刺绣妈妈包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 双肩背包 | 牛津布",
    image_url: "https://img.alicdn.com/imgextra/i1/2836045535/O1CN01Ii5q9d1ql4xdv4P3t_!!2836045535.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "双肩背包",
    price: "¥118.00"
  },
  {
    product_id: 1021,
    title: "香港真皮腋下包包2023新款时尚百搭单肩包小众设计高级感轻奢女包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 真皮",
    image_url: "https://img.alicdn.com/imgextra/i2/3189540051/O1CN01u2ywAb1CFP1lVKB2w_!!3189540051.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥279.00"
  },
  {
    product_id: 1022,
    title: "LORO PIANA/诺悠翩雅女包Extra Pocket L19盒子包拉链手提斜挎包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 盒子包",
    image_url: "https://img.alicdn.com/imgextra/i3/3483202335/O1CN01ysfeNr1T7TdduLjhy_!!3483202335.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥599.00"
  },
  {
    product_id: 1023,
    title: "2023斜挎肩日系韩版潮ins网红绣花帆布古风汉服小包包女包新款",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 通用款女包 | 帆布",
    image_url: "https://img.alicdn.com/imgextra/img/ibank/O1CN01r8ySbG1R2JoFlkSoF_!!3917572053-0-cib.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "通用款女包",
    price: "¥109.00"
  },
  {
    product_id: 1024,
    title: "法国专柜MDITCK~休闲通勤双肩包女新款2023牛津布防盗背包大容量",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 双肩背包 | 通勤",
    image_url: "https://img.alicdn.com/imgextra/i3/2212408601399/O1CN01OORxJV1MCmvG7xrXR_!!2212408601399.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "双肩背包",
    price: "¥259.00"
  },
  {
    product_id: 1025,
    title: "原创疯马皮新款胸包大容量单肩斜挎包休闲个性牛皮男包真皮背包潮",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 男士包袋 | 疯马皮",
    image_url: "https://img.alicdn.com/imgextra/i1/37814467/O1CN01N55JCp1irvr9Ld2qZ_!!37814467.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "男士包袋",
    price: "¥198.00"
  },
  {
    product_id: 1026,
    title: "外贸真皮牛皮凯旋门购物袋妈咪包高品质通勤时尚锁头单肩托特女包",
    description: "服饰时尚 | 箱包服配 | 箱包 | 包袋 | 托特包 | 通勤时尚",
    image_url: "https://img.alicdn.com/imgextra/i2/2211764816675/O1CN01zrjlC61zBCULaiFkx_!!2211764816675.jpg",
    industry: "服饰时尚",
    cate1: "箱包服配",
    cate2: "箱包",
    cate3: "包袋",
    cate4: "托特包",
    price: "¥329.00"
  }
];

const MOCK_PHONE_PRODUCTS: MockProduct[] = [
  {
    product_id: 1007,
    title: "Huawei/华为 MATE 30 5G官方旗舰原装正品mate30pro鸿蒙智能手机",
    description: "3C数码 | 手机 | 手机 | 手机 | 品牌:华为 | 型号:Mate 30 Pro",
    image_url: "https://img.alicdn.com/imgextra/i1/3051991189/O1CN01V6JqvO1KebkWkVyfv_!!3051991189.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥1999.00"
  },
  {
    product_id: 2001,
    title: "Apple/苹果11全网通4G正品iPhoneXR双卡便宜促销备用学生二手手机",
    description: "3C数码 | 手机 | 二手手机 | Apple iPhone XR/11",
    image_url: "https://img.alicdn.com/imgextra/i2/3017748404/O1CN01iCm9od2Bx5Lj1BkLu_!!3017748404.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "二手手机",
    price: "¥1499.00"
  },
  {
    product_id: 2002,
    title: "新款Huawei/华为 nova 10z鸿蒙系统官方正品双卡双待直屏手机分期",
    description: "3C数码 | 手机 | 华为 nova 10z | 鸿蒙",
    image_url: "https://img.alicdn.com/imgextra/i4/417378894/O1CN016oBrgG2FZVP8vBkRR_!!417378894.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥1699.00"
  },
  {
    product_id: 2003,
    title: "HONOR/荣耀X40i 5G手机 40W快充 5000万超清影像 学生拍照电竞手机",
    description: "3C数码 | 手机 | 荣耀 X40i | 5G 快充",
    image_url: "https://img.alicdn.com/imgextra/i2/1730436394/O1CN01nCB4Kz1x6VDPgQIFz_!!0-item_pic.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥1799.00"
  },
  {
    product_id: 2004,
    title: "【全国联保】荣耀60 骁龙778G 双卡5g 1亿像素影像 66W超级快充",
    description: "3C数码 | 手机 | 荣耀 60 | 5G",
    image_url: "https://img.alicdn.com/imgextra/i1/507957984/O1CN01icovBO28qiurHOH3N_!!0-item_pic.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2299.00"
  },
  {
    product_id: 2005,
    title: "OPPO Reno9 Pro+5G手机原装正品新款旗舰",
    description: "3C数码 | 手机 | OPPO Reno9 Pro+ | 5G",
    image_url: "https://img.alicdn.com/imgextra/i3/2212974746665/O1CN01CZHvAd1z6cZt43eLH_!!2212974746665.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2899.00"
  },
  {
    product_id: 2006,
    title: "iPhone13国行正品5G学生手机13promax特价Apple苹果13pro二手手机",
    description: "3C数码 | 手机 | iPhone 13 Pro Max | 二手手机",
    image_url: "https://img.alicdn.com/imgextra/i4/2209809345816/O1CN01dSN3AL1spmJTlB40C_!!2209809345816.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "二手手机",
    price: "¥3399.00"
  },
  {
    product_id: 2007,
    title: "24期免息vivo S16e新品旗舰5G智能拍照游戏电竞手机",
    description: "3C数码 | 手机 | vivo S16e | 5G",
    image_url: "https://img.alicdn.com/imgextra/i4/1659902905/O1CN01Tg1h7t1XKXNGEGrJE_!!0-item_pic.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2099.00"
  },
  {
    product_id: 2008,
    title: "Apple/苹果 iPhone SE (第二代)苹果SE2正品学生SE工作便宜备用机",
    description: "3C数码 | 手机 | iPhone SE2 | 备用机",
    image_url: "https://img.alicdn.com/imgextra/i1/2023088368/O1CN01ZlesuL2Bgb5e8PqaE_!!2023088368.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥1199.00"
  },
  {
    product_id: 2009,
    title: "【全国联保】vivo Y74S 星夜黑 8GB+256GB 44W闪充 5G手机",
    description: "3C数码 | 手机 | vivo Y74S | 5G",
    image_url: "https://img.alicdn.com/imgextra/i1/507957984/O1CN01eY46rH28qizcQuGIk_!!0-item_pic.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥1699.00"
  },
  {
    product_id: 2010,
    title: "Apple/苹果 iPhone 11 苹果11 全网通手机 正品现货",
    description: "3C数码 | 手机 | iPhone 11",
    image_url: "https://img.alicdn.com/imgextra/i3/100340983/O1CN01kUCWya1J8G5EchH80_!!100340983.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2299.00"
  },
  {
    product_id: 2011,
    title: "【咨询更优惠】Apple/苹果 iPhone 14 Pro 苹果14 灵动岛送货上门",
    description: "3C数码 | 手机 | iPhone 14 Pro",
    image_url: "https://img.alicdn.com/imgextra/i1/2214646624342/O1CN01WZnK1r1hwgV0vwFmR_!!2214646624342.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥5299.00"
  },
  {
    product_id: 2012,
    title: "Huawei/华为 Huawei Mate 30/PRO 5G原装麒麟990双模鸿蒙系统",
    description: "3C数码 | 手机 | 华为 Mate 30 Pro | 麒麟990",
    image_url: "https://img.alicdn.com/imgextra/i4/1074798046/O1CN01oUpDCW29J7W3WH5o8_!!1074798046.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2599.00"
  },
  {
    product_id: 2013,
    title: "Samsung/三星 Galaxy S20 FE 5G 骁龙865双模拍照5G手机",
    description: "3C数码 | 手机 | 三星 Galaxy S20 FE | 5G",
    image_url: "https://img.alicdn.com/imgextra/i1/3458019384/O1CN01r2XM5P2JBvQfqpReC_!!3458019384.png",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2699.00"
  },
  {
    product_id: 2014,
    title: "HONOR/荣耀80 GT新品手机上市官方旗舰店正品新品旗舰5G智能拍照游戏电竞手机",
    description: "3C数码 | 手机 | 荣耀 80 GT | 5G 电竞",
    image_url: "https://img.alicdn.com/imgextra/i4/2205748077959/O1CN01aObQcG28fH5jLwBKA_!!0-item_pic.jpg",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥2499.00"
  },
  {
    product_id: 2015,
    title: "现货顺丰速发】苹果14 plus手机官方旗舰店国行正品5G全网通新品苹果14手机",
    description: "3C数码 | 手机 | iPhone 14 Plus | 5G",
    image_url: "https://img.alicdn.com/imgextra/i3/2201415902533/O1CN01Xtz61V1UaA21OiSRx_!!2-item_pic.png",
    industry: "3C数码",
    cate1: "手机",
    cate2: "手机",
    cate3: "手机",
    cate4: "手机",
    price: "¥4799.00"
  }
];

const MOCK_MARTIN_BOOT_PRODUCTS: MockProduct[] = [
  {
    product_id: 3001,
    title: "漫步樱空欧韩真皮马丁靴短筒牛皮靴子厚底英伦风女靴米色短靴5566",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 马丁靴 | 英伦风",
    image_url: "https://img.alicdn.com/imgextra/i3/1945272358/O1CN01rzuEgs1TI0hbnNPSo_!!1945272358.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "马丁靴",
    price: "¥269.00"
  },
  {
    product_id: 3002,
    title: "Daphne/达芙妮往年款潮酷黑色中性双拉链马丁靴舒适保暖圆头女靴",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 马丁靴 | 保暖",
    image_url: "https://img.alicdn.com/imgextra/i4/1596191928/O1CN01syoMxW1Q74Lvs4cfF_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "马丁靴",
    price: "¥219.00"
  },
  {
    product_id: 3003,
    title: "马丁靴女英伦风2022冬季新款小个子百搭厚底加绒机车短靴单靴子潮",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 马丁靴 | 冬季加绒",
    image_url: "https://img.alicdn.com/imgextra/i1/2311027271/O1CN01EkCJuY23aAaGc8fdQ_!!2311027271.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "马丁靴",
    price: "¥239.00"
  },
  {
    product_id: 3004,
    title: "公羊博士女鞋冬季加绒加厚保暖棉鞋女士外穿高颜值真皮鞋子马丁靴",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 马丁靴 | 真皮",
    image_url: "https://img.alicdn.com/imgextra/i2/2213292409341/O1CN01WbuYMG2IsET9ut3zi_!!2213292409341.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "马丁靴",
    price: "¥329.00"
  },
  {
    product_id: 3005,
    title: "不过膝系带长筒靴女2022年秋季新款粗跟加绒厚底真皮高筒靴骑士靴",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 马丁靴相关",
    image_url: "https://img.alicdn.com/imgextra/i4/1673487671/O1CN01ggwJ2626XN08In6dd_!!1673487671.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "马丁靴",
    price: "¥299.00"
  },
  {
    product_id: 3006,
    title: "欧美流行潮牌新款百搭真皮雕花切尔西短靴复古英伦风马丁靴男女",
    description: "服饰时尚 | 男女鞋 | 男鞋 | 靴子 | 切尔西靴 | 马丁靴",
    image_url: "https://img.alicdn.com/imgextra/i4/1761286714/O1CN01efDux51zT3t3jmC3R_!!1761286714.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "男鞋",
    cate3: "靴子",
    cate4: "切尔西靴",
    price: "¥359.00"
  },
  {
    product_id: 3007,
    title: "冬季加绒保暖切尔西靴男中帮短靴百搭布洛克雕花高帮真皮马丁靴男",
    description: "服饰时尚 | 男女鞋 | 男鞋 | 靴子 | 切尔西靴 | 保暖",
    image_url: "https://img.alicdn.com/imgextra/i1/3009857086/O1CN01sW1APJ22DRIzZJPw9_!!3009857086.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "男鞋",
    cate3: "靴子",
    cate4: "切尔西靴",
    price: "¥339.00"
  },
  {
    product_id: 3008,
    title: "短靴男春季2023新款英伦风工装马丁靴低帮板鞋大头皮鞋男鞋潮鞋子",
    description: "服饰时尚 | 男女鞋 | 男鞋 | 靴子 | 时装靴 | 马丁靴",
    image_url: "https://img.alicdn.com/imgextra/i1/2209728543019/O1CN01l4NXCt1YAkXepsiFt_!!2209728543019.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "男鞋",
    cate3: "靴子",
    cate4: "时装靴",
    price: "¥189.00"
  },
  {
    product_id: 3009,
    title: "千百度2021冬款切尔西靴时尚潮流圆头短筒靴烟筒靴A21531509",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 烟筒靴",
    image_url: "https://img.alicdn.com/imgextra/i1/867160039/O1CN01vOWr9i1C9uGu6zREP_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "烟筒靴",
    price: "¥279.00"
  },
  {
    product_id: 3010,
    title: "撤柜断码处理2019秋冬款真皮女鞋中粗跟后拉链简约牛皮加绒短靴子",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 时装靴 | 秋冬",
    image_url: "https://img.alicdn.com/imgextra/i2/1752138249/O1CN01BatYNd2Ao5isoGlg8_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "时装靴",
    price: "¥249.00"
  },
  {
    product_id: 3011,
    title: "【樱夏社】粗跟弹力瘦瘦靴2022秋冬新款韩版方头侧拉链磨砂短靴女",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 弹力靴/袜靴",
    image_url: "https://img.alicdn.com/imgextra/i3/2367732848/O1CN01TiOr9b1WuQiS9Ckaz_!!2367732848.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "弹力靴/袜靴",
    price: "¥229.00"
  },
  {
    product_id: 3012,
    title: "HARSON哈森圆头休闲时装靴2022冬专柜促销方跟通勤女短靴HA222530",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 时装靴 | 通勤",
    image_url: "https://img.alicdn.com/imgextra/i4/345014945/O1CN01P5dkyx1mOrKwqb1H2_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "时装靴",
    price: "¥369.00"
  },
  {
    product_id: 3013,
    title: "震地王薄款网纱长靴女2023新款春夏网面厚底凉靴透气镂空高筒靴子",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 时装靴 | 春夏",
    image_url: "https://img.alicdn.com/imgextra/i2/4205548644/O1CN01AZVOSO2Dj0PxDSnfN_!!0-item_pic.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "时装靴",
    price: "¥199.00"
  },
  {
    product_id: 3014,
    title: "丹麦撤柜切尔西靴2022冬款女短靴厚底头层牛皮中筒靴 新潮 216223",
    description: "服饰时尚 | 男女鞋 | 女鞋 | 靴子 | 切尔西靴",
    image_url: "https://img.alicdn.com/imgextra/i3/144182092/O1CN01EdiazL1RKBMRbwhUE_!!144182092.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "女鞋",
    cate3: "靴子",
    cate4: "切尔西靴",
    price: "¥319.00"
  },
  {
    product_id: 3015,
    title: "断码清仓处理真皮特价男鞋头层牛皮圆头侧拉链羊毛保暖厚底男靴",
    description: "服饰时尚 | 男女鞋 | 男鞋 | 高帮鞋 | 男靴 | 保暖",
    image_url: "https://img.alicdn.com/imgextra/i2/169896164/O1CN01sVXDpW1vP9z3Y05TM_!!169896164.jpg",
    industry: "服饰时尚",
    cate1: "男女鞋",
    cate2: "男鞋",
    cate3: "高帮鞋",
    cate4: "高帮鞋",
    price: "¥289.00"
  }
];

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function toDistance(similarity: number): number {
  const s = Math.max(0, Math.min(1, similarity));
  return Math.round((1 - s) * 64);
}

function toRetrievalItem(product: MockProduct, similarity: number): RetrievalItem {
  return {
    product_id: product.product_id,
    score: toDistance(similarity),
    payload: {
      title: product.title,
      description: product.description,
      image_url: product.image_url,
      price: product.price,
      category_ids: [product.cate1, product.cate2, product.cate3, product.cate4]
    }
  };
}

function buildResponse(items: RetrievalItem[], diagnostics: Record<string, unknown>): RetrievalResponse {
  return {
    request_id: `mock_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    latency_ms: Math.floor(20 + Math.random() * 60),
    results: items,
    diagnostics
  };
}

function rankByBaseProduct(base: MockProduct, topK: number): RetrievalItem[] {
  const sameCate1 = MOCK_PRODUCTS.filter((p) => p.product_id !== base.product_id && p.cate1 === base.cate1);
  const sameIndustry = MOCK_PRODUCTS.filter((p) => p.product_id !== base.product_id && p.industry === base.industry);
  const candidatePool = sameCate1.length > 0 ? sameCate1 : sameIndustry;

  const ranked = candidatePool
    .map((p) => {
      let score = 0.2;
      if (p.industry === base.industry) score += 0.3;
      if (p.cate1 === base.cate1) score += 0.2;
      if (p.cate4 === base.cate4) score += 0.2;
      if (p.title.includes("新款") && base.title.includes("新款")) score += 0.05;
      if (p.title.includes("运动") && base.title.includes("运动")) score += 0.05;
      return { p, sim: Math.min(score, 0.95) };
    })
    .sort((a, b) => b.sim - a.sim)
    .slice(0, topK)
    .map(({ p, sim }) => toRetrievalItem(p, sim));

  return ranked.slice(0, topK);
}

function inferDomainByFilename(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("shoe") || n.includes("鞋")) return "鞋";
  if (n.includes("bag") || n.includes("包")) return "包";
  if (n.includes("phone") || n.includes("手机")) return "手机";
  if (n.includes("hat") || n.includes("帽")) return "帽";
  return "通用";
}

function rankByText(query: string, topK: number): RetrievalItem[] {
  const tokens = query
    .trim()
    .toLowerCase()
    .split(/[\s,，。!！?？;；/|]+/)
    .filter(Boolean);

  const scored = MOCK_PRODUCTS
    .map((p) => {
      const text = `${p.title} ${p.description} ${p.cate1} ${p.cate2} ${p.cate3} ${p.cate4}`.toLowerCase();
      let hit = 0;
      for (const t of tokens) {
        if (text.includes(t)) hit += 1;
      }
      const sim = tokens.length > 0 ? Math.min(0.2 + hit / tokens.length * 0.7, 0.95) : 0.2;
      return { p, sim };
    });

  // Keep results category-consistent with the strongest matched category.
  const cate1Counter = new Map<string, number>();
  for (const row of scored) {
    if (row.sim > 0.2) {
      cate1Counter.set(row.p.cate1, (cate1Counter.get(row.p.cate1) ?? 0) + 1);
    }
  }
  const dominantCate1 = Array.from(cate1Counter.entries()).sort((a, b) => b[1] - a[1])[0]?.[0];
  const filtered = dominantCate1 ? scored.filter((row) => row.p.cate1 === dominantCate1) : scored;

  const ranked = filtered
    .sort((a, b) => b.sim - a.sim)
    .slice(0, topK)
    .map(({ p, sim }) => toRetrievalItem(p, sim));

  return ranked;
}

export async function listDisplayProducts(limit: number): Promise<ProductDisplayItem[]> {
  await sleep(120);
  const safeLimit = Math.max(1, Math.min(limit, 100));
  const selectable = MOCK_PRODUCTS.filter((p) => p.cate1 === "箱包服配" && p.cate3 === "包袋");
  return selectable.slice(0, safeLimit).map((p) => ({
    product_id: p.product_id,
    title: p.title,
    description: p.description,
    image_url: p.image_url
  }));
}

export async function similarByProduct(productId: number, topK: number): Promise<RetrievalResponse> {
  await sleep(220);
  const base = MOCK_PRODUCTS.find((p) => p.product_id === productId) ?? MOCK_PRODUCTS[0];
  const targetK = Math.max(15, topK);
  return buildResponse(rankByBaseProduct(base, targetK), {
    mode: "mock-similar-product",
    category_lock: base.cate1,
    source: "local-mock-data"
  });
}

export async function similarByImage(file: File, topK: number): Promise<RetrievalResponse> {
  await sleep(260);
  const domain = inferDomainByFilename(file.name);
  const pool =
    domain === "鞋" ? MOCK_PRODUCTS.filter((p) => p.cate1 === "男女鞋") :
    domain === "包" ? MOCK_PRODUCTS.filter((p) => p.cate1 === "箱包服配" && p.cate3 === "包袋") :
    domain === "手机" ? MOCK_PRODUCTS.filter((p) => p.cate1 === "手机") :
    domain === "帽" ? MOCK_PRODUCTS.filter((p) => p.cate3.includes("帽")) :
    MOCK_PRODUCTS.filter((p) => p.cate1 === "女装");
  const items = pool.slice(0, topK).map((p, i) => toRetrievalItem(p, Math.max(0.92 - i * 0.08, 0.35)));
  return buildResponse(items, {
    mode: "mock-similar-image",
    inferred_domain: domain,
    source: "local-mock-data"
  });
}

export async function photoSearch(file: File, topK: number): Promise<RetrievalResponse> {
  await sleep(280);
  const k = Math.max(15, topK);
  const items = MOCK_PHONE_PRODUCTS
    .slice(0, k)
    .map((p, i) => toRetrievalItem(p, Math.max(0.95 - i * 0.04, 0.35)));
  return buildResponse(items, {
    mode: "mock-photo-search",
    related_to_product_id: 1007,
    category_lock: "手机",
    source: "local-mbe-phone-mock-data",
    uploaded_file_name: file.name || "uploaded_image"
  });
}

export async function textSearch(queryText: string, topK: number): Promise<RetrievalResponse> {
  await sleep(240);
  const normalized = queryText.trim().toLowerCase();
  const martinBootQuery = /马丁靴|靴子|短靴|切尔西|英伦/.test(normalized);
  const k = Math.max(15, topK);
  const items = martinBootQuery
    ? MOCK_MARTIN_BOOT_PRODUCTS.slice(0, k).map((p, i) => toRetrievalItem(p, Math.max(0.96 - i * 0.04, 0.35)))
    : rankByText(queryText, k);
  return buildResponse(items, {
    mode: "mock-text-search",
    query: queryText,
    source: martinBootQuery ? "local-mbe-martin-boot-mock-data" : "local-mock-data",
    category_lock: martinBootQuery ? "马丁靴/靴子" : undefined
  });
}
