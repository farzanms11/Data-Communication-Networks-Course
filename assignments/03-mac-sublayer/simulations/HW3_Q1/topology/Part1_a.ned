package topology;
import inet.node.ethernet.EthernetHost;
import inet.node.ethernet.EthernetHub;
import inet.node.ethernet.Eth10M;

network Part1_a
{
    @display("bgb=1000,500");
    submodules:
        host1: EthernetHost {
            @display("p=150,100");
        }
        host2: EthernetHost {
            @display("p=150,200");
        }
        host3: EthernetHost {
            @display("p=150,300");
        }
        host4: EthernetHost {
            @display("p=150,400");
        }
        host5: EthernetHost {
            @display("p=850,100");
        }
        host6: EthernetHost {
            @display("p=850,200");
        }
        host7: EthernetHost {
            @display("p=850,300");
        }
        host8: EthernetHost {
            @display("p=850,400");
        }
        server1: EthernetHost {
            @display("p=500,50");
        }
        server2: EthernetHost {
            @display("p=500,450");
        }
        hub1: EthernetHub {
            @display("p=500,150");
        }
        hub2: EthernetHub {
            @display("p=500,250");
        }
        hub3: EthernetHub {
            @display("p=500,350");
        }
    connections:
        host1.ethg <--> Eth10M{length = 10m;} <--> hub1.ethg++;
        host2.ethg <--> Eth10M{length = 10m;} <--> hub2.ethg++;
        host3.ethg <--> Eth10M{length = 10m;} <--> hub2.ethg++;
        host4.ethg <--> Eth10M{length = 10m;} <--> hub3.ethg++;
        host5.ethg <--> Eth10M{length = 10m;} <--> hub1.ethg++;
        host6.ethg <--> Eth10M{length = 10m;} <--> hub2.ethg++;
        host7.ethg <--> Eth10M{length = 10m;} <--> hub2.ethg++;
        host8.ethg <--> Eth10M{length = 10m;} <--> hub3.ethg++;
        server1.ethg <--> Eth10M{length = 10m;} <--> hub1.ethg++;
        server2.ethg <--> Eth10M{length = 10m;} <--> hub3.ethg++;
        hub1.ethg++ <--> Eth10M{length = 10m;} <--> hub2.ethg++;
        hub3.ethg++ <--> Eth10M{length = 10m;} <--> hub2.ethg++;
}