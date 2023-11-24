docker inspect 容器|grep Pid
ln -s /proc/容器进程号/ns/net /var/run/netns/容器
ip netns exec ..