#!/bin/bash

src=list.txt
dest=listx.txt
tmp=/tmp/gfwlist.txt

sed -n '/!############## Custom List Start ##############/,/!############### Custom List End ###############/p' $dest > $tmp
sed "/!---------------------EOF-----------------------/e cat $tmp" $src > $dest
rm $tmp
