# ip 本地端口 远程端口
while true
do
  ssh -p 5102 "$1" -L "$2":127.0.0.1:"$3" -N
done