package topology;
import inet.networks.base.WiredNetworkBase;
import inet.node.ethernet.EthernetLink;
import inet.node.inet.StandardHost;

network Part1 extends WiredNetworkBase
{
    @display("bgb=1000,500");
    submodules:
        source: StandardHost {
            @display("p=250,250");
        }
        destination: StandardHost {
            @display("p=750,250");
        }
    connections:
        source.ethg++ <--> EthernetLink <--> destination.ethg++;
}