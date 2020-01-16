while true
do
  ssh -p 5102 zihao_wang@"$1" -L "$2":127.0.0.1:"$2" -N
done
