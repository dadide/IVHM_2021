FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get install -y python3-pip 
RUN pip3 install --upgrade pip
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy 
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple matplotlib
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple scipy
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple numba
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple cantools


RUN apt-get install -y libusb-1.0-0

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install tzdata
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN dpkg-reconfigure -f noninteractive tzdata

ADD IVHM.tar.gz ./IVHM

WORKDIR /IVHM
RUN chmod +x runpyfinal.sh
ENTRYPOINT ["/IVHM/runpyfinal.sh"]

#sudo docker build -f df19 -t env_truetime:2.0 .
#/home/efc/SAICSJTU:/IVHM,/dev/bus/usb/001/002:/dev/bus/usb/001/002






