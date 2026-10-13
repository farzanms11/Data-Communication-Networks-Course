package topology;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.ethernet.EthernetSwitch;
import inet.node.ethernet.Eth10M;
import inet.node.inet.StandardHost;


network VLAN
{
    @display("bgb=1000,500");
    submodules:
        host1: StandardHost {
            @display("p=150,175");
        }
        host2: StandardHost {
            @display("p=150,325");
        }
        host3: StandardHost {
            @display("p=375,440");
        }
        host4: StandardHost {
            @display("p=625,440");
        }
        host5: StandardHost {
            @display("p=375,50");
        }
        host6: StandardHost {
            @display("p=625,50");
        }
        host7: StandardHost {
            @display("p=850,175");
        }
        host8: StandardHost {
            @display("p=850,325");
        }
        Switch4: EthernetSwitch {
            @display("p=500,150");
        }
        Switch2: EthernetSwitch {
            @display("p=500,350");
        }
        Switch1: EthernetSwitch {
            @display("p=300,250");
        }
        Switch3: EthernetSwitch {
            @display("p=700,250");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=850,50;is=s");
        }
    connections:
        host1.ethg++ <--> Eth10M {  length = 10m; } <--> Switch1.ethg++;
        host2.ethg++ <--> Eth10M {  length = 10m; } <--> Switch1.ethg++;
        host3.ethg++ <--> Eth10M {  length = 10m; } <--> Switch2.ethg++;
        host4.ethg++ <--> Eth10M {  length = 10m; } <--> Switch2.ethg++;
        host5.ethg++ <--> Eth10M {  length = 10m; } <--> Switch4.ethg++;
        host6.ethg++ <--> Eth10M {  length = 10m; } <--> Switch4.ethg++;
        host7.ethg++ <--> Eth10M {  length = 10m; } <--> Switch3.ethg++;
        host8.ethg++ <--> Eth10M {  length = 10m; } <--> Switch3.ethg++;
        Switch1.ethg++ <--> Eth10M {  length = 10m; } <--> Switch2.ethg++;
        Switch1.ethg++ <--> Eth10M {  length = 10m; } <--> Switch4.ethg++;
        Switch2.ethg++ <--> Eth10M {  length = 10m; } <--> Switch3.ethg++;
}
