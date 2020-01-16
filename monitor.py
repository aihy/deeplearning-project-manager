import re
import xml.dom.minidom

from requests import get

from app import db, Server, GpuMonitor, Port


def begin_monit():
    dp = re.compile(r"\d+")
    r_list = Server.query.all()
    for it in r_list:
        server_ip = it.serverIp
        ac_port = Port.query.filter_by(serverIp=server_ip, type="flask").first().port
        get_xml = get("http://127.0.0.1:" + str(ac_port) + "/nvidia")
        newdom = xml.dom.minidom.parseString(get_xml.text)
        newroot = newdom.documentElement
        newb = newroot.getElementsByTagName("gpu")
        num_of_gpus = len(newb)
        # 查询服务器表，如果gpu数量不一致就更新
        r_s = Server.query.filter_by(serverIp=server_ip).first()
        if r_s.gpuAmount != num_of_gpus:
            r_s.gpuAmount = num_of_gpus
            db.session.commit()
        for i in range(num_of_gpus):
            product_name = newb[i].getElementsByTagName("product_name")[0].firstChild.data
            fan_speed = newb[i].getElementsByTagName("fan_speed")[0].firstChild.data
            if fan_speed == "N/A":
                fan_speed = "0"
            fan_speed = dp.findall(fan_speed)[0]
            fb_memory_usage_total = newb[i].getElementsByTagName("fb_memory_usage")[0].getElementsByTagName("total")[
                0].firstChild.data
            fb_memory_usage_total = dp.findall(fb_memory_usage_total)[0]
            fb_memory_usage_used = newb[i].getElementsByTagName("fb_memory_usage")[0].getElementsByTagName("used")[
                0].firstChild.data
            fb_memory_usage_used = dp.findall(fb_memory_usage_used)[0]
            fb_memory_usage_free = newb[i].getElementsByTagName("fb_memory_usage")[0].getElementsByTagName("free")[
                0].firstChild.data
            fb_memory_usage_free = dp.findall(fb_memory_usage_free)[0]
            utilization_gpu_util = newb[i].getElementsByTagName("utilization")[0].getElementsByTagName("gpu_util")[
                0].firstChild.data
            utilization_gpu_util = dp.findall(utilization_gpu_util)[0]
            utilization_gpu_temp = newb[i].getElementsByTagName("temperature")[0].getElementsByTagName("gpu_temp")[
                0].firstChild.data
            utilization_gpu_temp = dp.findall(utilization_gpu_temp)[0]
            gpu_item = GpuMonitor(serverIp=server_ip, gpuNumber=i, productName=product_name, fanSpeed=fan_speed,
                                  usageTotal=fb_memory_usage_total, usageUsed=fb_memory_usage_used,
                                  usageFree=fb_memory_usage_free, gpuUtil=utilization_gpu_util,
                                  gpuTemp=utilization_gpu_temp)
            db.session.add(gpu_item)
            db.session.commit()


if __name__ == "__main__":
    begin_monit()
