package topology;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.ethernet.Eth100M;
import inet.node.ethernet.EthernetSwitch;
import inet.node.inet.StandardHost;
import inet.visualizer.common.DataLinkVisualizer;
import inet.visualizer.common.IntegratedVisualizer;

network Part2
{
    @display("bgb=1200,600");
    submodules:
        visualizer: IntegratedVisualizer {
            @display("p=100,200");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=100,400");
        }
        etherSwitch1: EthernetSwitch {
            @display("p=550,150");
        }
        etherSwitch2: EthernetSwitch {
            @display("p=500,425");
        }
        etherSwitch3: EthernetSwitch {
            @display("p=950,275");
        }
        etherSwitch4: EthernetSwitch {
            @display("p=700,300");
        }
        etherSwitch5: EthernetSwitch {
            @display("p=850,150");
        }
        source1: StandardHost {
            @display("p=300,50");
        }
        source2: StandardHost {
            @display("p=275,175");
        }
        source3: StandardHost {
            @display("p=350,300");
        }
        destination1: StandardHost {
            @display("p=750,500");
        }
        destination2: StandardHost {
            @display("p=1050,400");
        }
        destination3: StandardHost {
            @display("p=725,50");
        }
        host1: StandardHost {
            @display("p=350,500");
        }
        host2: StandardHost {
            @display("p=1100,150");
        }
    connections:
        etherSwitch1.ethg++ <--> Eth100M <--> source1.ethg++;
        etherSwitch1.ethg++ <--> Eth100M <--> etherSwitch4.ethg++;
        etherSwitch1.ethg++ <--> Eth100M <--> source2.ethg++;
        etherSwitch1.ethg++ <--> Eth100M <--> source3.ethg++;
        etherSwitch2.ethg++ <--> Eth100M <--> host1.ethg++;
        etherSwitch2.ethg++ <--> Eth100M <--> etherSwitch4.ethg++;
        etherSwitch2.ethg++ <--> Eth100M <--> destination1.ethg++;
        etherSwitch3.ethg++ <--> Eth100M <--> etherSwitch4.ethg++;
        etherSwitch3.ethg++ <--> Eth100M <--> destination2.ethg++;
        etherSwitch3.ethg++ <--> Eth100M <--> host2.ethg++;
        etherSwitch4.ethg++ <--> Eth100M <--> etherSwitch5.ethg++;
        etherSwitch5.ethg++ <--> Eth100M <--> destination3.ethg++;
}