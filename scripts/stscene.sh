#!/bin/bash
# author: mrxirzzz

scenes=(1-CityParkCollec 2-ScasUrban 3-DownTown 4-FactoryDistrict 5-AbandonedCity 6-ModularNeighborhood 7-NordicHarbour 8-slums 9-TankCleaningCenter 10-ModularEuropean 11-facades 12-IndustrialArea 13-OldTown 14-ModernCity 15-yard3 16-NYC 17-TrainStation 18-Brushify 19-None 20-OldShipyard 21-ContainerYard 22-SteampunkEnvironment 23-UrbanJapan 24-HongKongStreet 25-CityDowntown 26-ModularCity)

# PREFIX1="CUDA_VISIBLE_DEVICES=1 bash "
PREFIX1="bash "
PREFIX2="-opengl -NOSOUND -WINDOWED -RexX=640 -RexY=480 -NoVSync -BENCHMARK -FPS=1000 --settings "

echo "Input scene_id:"
read id
$PREFIX1 ../scenes/${scenes[id-1]}/LinuxNoEditor/hi.sh $PREFIX2 settings/$(id).json &
	
