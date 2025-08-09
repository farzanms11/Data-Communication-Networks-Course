import inet.common.scenario.ScenarioManager;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.aodv.AodvRouter;
import inet.node.ethernet.Eth100M;
import inet.node.ethernet.EthernetSwitch;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import inet.node.inet.WirelessHost;
import inet.node.wireless.AccessPoint;
import inet.physicallayer.wireless.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;
import inet.visualizer.common.IntegratedVisualizer;
import inet.visualizer.common.NetworkRouteVisualizer;

network AODV
{
    parameters:
        @display("bgb=1006.008,801.19196");
		@statistic[numRcvdPk](source=count(source1.app[0].pingRxSeq); record=figure; targetFigure=numRcvdPkCounter; checkSignals=false);
        @figure[numRcvdPkCounter](type=counter; transform=scale(0.8); pos=80,300; label="Received ping replies"; decimalPlaces=4);
        @statistic[numLost](source=count(source1.app[0].numLost); record=figure; targetFigure=numLostPkCounter; checkSignals=false);
        @figure[numLostPkCounter](type=counter; transform=scale(0.8); pos=80,400; label="Pings lost"; decimalPlaces=4);

    submodules:
        source1: AodvRouter {
            @display("p=336.49,360.64");
        }
        aodvRouter1: AodvRouter {
            @display("p=440,107.87");
        }
        aodvRouter2: AodvRouter {
            @display("p=550,107.87");
        }
        aodvRouter3: AodvRouter {
            @display("p=359.03,569.94");
        }
        aodvRouter4: AodvRouter {
            @display("p=304.29,474.95");
        }
        aodvRouter5: AodvRouter {
            @display("p=595.7,569.94");
        }
        aodvRouter6: AodvRouter {
            @display("p=483,603.75");
        }
        destination: AodvRouter {
            @display("p=627.9,360.64");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=924,74");
        }
        visualizer: IntegratedVisualizer {
            @display("p=923,180");
        }
        radioMedium: Ieee80211ScalarRadioMedium {
            @display("p=923,283");
        }
        aodvRouter7: AodvRouter {
            @display("p=658.49,474.95");
        }
}
