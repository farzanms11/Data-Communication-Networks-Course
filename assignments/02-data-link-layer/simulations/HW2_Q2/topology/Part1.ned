package topology;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.ethernet.Eth100M;
import inet.node.inet.StandardHost;
import inet.visualizer.common.DataLinkVisualizer;

network Part1
{
    @display("bgb=1000,500");
    submodules:
        linkVisualizer: DataLinkVisualizer {
            @display("p=100,150");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=100,350");
        }
        wiredSource: StandardHost {
            @display("p=300,250");
        }
        wiredDestination: StandardHost {
            @display("p=800,250");
        }
    connections:
        wiredSource.ethg++ <--> Eth100M <--> wiredDestination.ethg++;
}
