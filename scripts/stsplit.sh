#!/bin/bash
# author: mrxirzzz

scenes=(1-CityParkCollec 2-ScasUrban 3-DownTown 4-FactoryDistrict 5-AbandonedCity 6-ModularNeighborhood 7-NordicHarbour 8-slums 9-TankCleaningCenter 10-ModularEuropean 11-facades 12-IndustrialArea 13-OldTown 14-ModernCity 15-yard3 16-NYC 17-TrainStation 18-Brushify 19-None 20-OldShipyard 21-ContainerYard 22-SteampunkEnvironment 23-UrbanJapan 24-HongKongStreet 25-CityDowntown 26-ModularCity)
# train scenes load
train=(10 11 12 14 16 17 1 20 22 23 25 26 2 3 4 5 8)
# val_seen scenes load
val_seen=(10 11 12 14 16 17 1 20 23 26 2 3 5 8)
# val_unseen scenes load
val_unseen=(13 24 6 9)
# test scenes load
testx=(15 18 21 7)
# all
all=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 20 21 22 23 24 25 26)

# PREFIX1="CUDA_VISIBLE_DEVICES=1 bash "
PREFIX1="bash "
PREFIX2="-opengl -NOSOUND -WINDOWED -RexX=640 -RexY=480 -NoVSync -BENCHMARK -FPS=1000 --settings "

echo "Input split:"
read split 
if [ $split == train ]
then
	for i in ${train[*]}
	do
		$PREFIX1 ../scenes/${scenes[i-1]}/hi.sh $PREFIX2 settings/$(i-1).json &
  	done
elif [ $split == val_seen ]
then
	for i in ${val_seen[*]}
	do
		$PREFIX1 ../scenes/${scenes[i-1]}/hi.sh $PREFIX2 settings/$(i-1).json &
  	done
elif [ $split == val_unseen ]
then
	for i in ${val_unseen[*]}
	do
		$PREFIX1 ../scenes/${scenes[i-1]}/hi.sh $PREFIX2 settings/$(i-1).json &
  	done
elif [ $split == testx ]
then
	for i in ${testx[*]}
	do
		$PREFIX1 ../scenes/${scenes[i-1]}/hi.sh $PREFIX2 settings/$(i-1).json &
  	done
else
	for i in ${all[*]}
	do
		$PREFIX1 ../scenes/${scenes[i-1]}/hi.sh $PREFIX2 settings/$(i-1).json &
  	done
fi
	
