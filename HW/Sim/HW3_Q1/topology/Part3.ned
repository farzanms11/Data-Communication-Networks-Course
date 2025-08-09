package topology;
import inet.node.ethernet.EthernetHost;
import inet.node.ethernet.EthernetSwitch;
import inet.node.ethernet.Eth10M;
import inet.visualizer.common.IntegratedVisualizer;
import inet.visualizer.contract.IIntegratedVisualizer;


network Part3
{
    @display("bgb=1100,500");
    submodules:
        host1: EthernetHost {
            parameters:
                @display("p=150,100");
        }
        host2: EthernetHost {
            parameters:
                @display("p=150,200");
        }
        host3: EthernetHost {
            parameters:
                @display("p=150,300");
        }
        host4: EthernetHost {
            parameters:
                @display("p=150,400");
        }
        host5: EthernetHost {
            parameters:
                @display("p=850,100");
        }
        host6: EthernetHost {
            parameters:
                @display("p=850,200");
        }
        host7: EthernetHost {
            parameters:
                @display("p=850,300");
        }
        host8: EthernetHost {
            parameters:
                @display("p=850,400");
        }
        server1: EthernetHost {
            parameters:
                @display("p=500,50");
        }
        server2: EthernetHost {
            parameters:
                @display("p=500,450");
        }
        ethernetSwitch1: EthernetSwitch {
            @display("p=500,150");
        }
        ethernetSwitch2: EthernetSwitch {
            @display("p=500,250");
        }
        ethernetSwitch3: EthernetSwitch {
            @display("p=500,350");
        }
        visualizer: IntegratedVisualizer {
            @display("p=1000,250");
        }
    connections:
        host1.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch1.ethg++;
        host2.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch2.ethg++;
        host3.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch2.ethg++;
        host4.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch3.ethg++;
        host5.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch1.ethg++;
        host6.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch2.ethg++;
        host7.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch2.ethg++;
        host8.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch3.ethg++;
        server1.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch1.ethg++;
        server2.ethg <--> Eth10M {  length = 10m; } <--> ethernetSwitch3.ethg++;
        ethernetSwitch1.ethg++ <--> Eth10M {  length = 10m; } <--> ethernetSwitch2.ethg++;
        ethernetSwitch3.ethg++ <--> Eth10M {  length = 10m; } <--> ethernetSwitch2.ethg++;
}
