//
//  MonitorModel.swift
//  Xlog解压工具
//
//  Created by kaoji on 2021/1/30.
//  Copyright © 2021 Damon. All rights reserved.
//

struct MonitorModel {
    var enterEvent = ""/// EnterRoom
    var sdkAppid = ""///应用标识
    var roomId = ""///房间Id
    var userId = ""///用户id
    var time = ""///来自日志的时间
    var timestamp = ""//日志时间转UNIX时间戳
    var dayMaxStamp = ""///当天最晚点的时间戳
}