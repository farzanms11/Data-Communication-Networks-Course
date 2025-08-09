


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


    submodules:
        source1: AodvRouter {
            @display("p=336.49,360.64");
        }
        aodvRouter1: AodvRouter {
            @display("p=441.14,107.87");
        }
        aodvRouter2: AodvRouter {
            @display("p=553.84,107.87");
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
            @display("p=925.688,118.472");
        }
        visualizer: IntegratedVisualizer {
            @display("p=925.688,196.784");
        }
        radioMedium: Ieee80211ScalarRadioMedium {
            @display("p=929.704,271.08");
        }
        aodvRouter7: AodvRouter {
            @display("p=658.49,474.95");
        }
}
