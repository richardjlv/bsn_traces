#include <map>
#include <string>
#include <vector>
#include <cmath>
#include <iostream>
#include <iomanip>
#define ROS_DEBUG(...) ((void)0)
namespace ros {namespace this_node {std::string getName(){return "/enactor";}}}
namespace archlib {struct AdaptationCommand{std::string source,target,action;};struct Exception{std::string source,target,content;};}
struct AdaptPub {std::vector<std::string> actions;void publish(const archlib::AdaptationCommand&m){actions.push_back(m.action);}};
struct ExceptPub {void publish(const archlib::Exception&) {}};
class Controller {public:
std::map<std::string,double> r_ref,r_curr,kp,freq;
std::map<std::string,int> exception_buffer,replicate_task;
std::map<std::string,std::vector<int>> invocations;
double stability_margin=.05;std::string adaptation_parameter="reliability";
AdaptPub adapt;ExceptPub except;
void apply_reli_strategy(const std::string&);
};
void Controller::apply_reli_strategy(const std::string &component) {
    ROS_DEBUG("r_ref[%s] = %.2f",component.c_str(),r_ref[component]);
    ROS_DEBUG("r_curr[%s] = %.2f",component.c_str(), r_curr[component]);
    ROS_DEBUG("kp[%s] = %.2f",component.c_str(), kp[component]);

    double error = r_ref[component] - r_curr[component]; //error = Rref - Rcurr

    if(error > stability_margin*r_ref[component] || error < stability_margin*r_ref[component]) {

        exception_buffer[component] = (exception_buffer[component] < 0) ? 0 : exception_buffer[component] + 1;

        if(component == "/g4t1"){
            // g4t1 reliability is inversely proportional to the sensors frequency
            /*
                Nota:

                -> Quando o componente é a Centralhub, adaptamos as frequências dos sensores. Porquê?
            */
            /*for (std::map<std::string, double>::iterator it = freq.begin(); it != freq.end(); ++it){
                if(it->first != "/g4t1"){
                    freq[it->first] += (error>0) ? ((-kp[it->first]/100) * error) : ((kp[it->first]/100) * error); 
                    if(freq[(it->first)] <= 0) break;
                    archlib::AdaptationCommand msg;
                    msg.source = ros::this_node::getName();
                    msg.target = it->first;
                    msg.action = "freq=" + std::to_string(freq[(it->first)]);
                    adapt.publish(msg);
                }
            }*/
            //double new_freq = freq[component] + ((error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error)); 
            double new_freq = freq[component] + ((kp[component]/100) * error);
            if(new_freq > 0) {
                freq[component] = new_freq;
                archlib::AdaptationCommand msg;
                msg.source = ros::this_node::getName();
                msg.target = component;
                msg.action = "freq=" + std::to_string(freq[component]);
                adapt.publish(msg);
                ROS_DEBUG("################################################");
                ROS_DEBUG("Adapting Centralhub");
                ROS_DEBUG("Action: %s", msg.action.c_str());
                ROS_DEBUG("################################################");
            } /*else {
                ROS_ERROR("COULD NOT ADAPT CENTRALHUB");
            }*/
        } else {
            if(adaptation_parameter == "replicate_collect") {
                replicate_task[component] += (error > 0) ? ceil(kp[component] * error) : floor(kp[component] * error);
                if (replicate_task[component] < 1) replicate_task[component] = 1;
                archlib::AdaptationCommand msg;
                msg.source = ros::this_node::getName();
                msg.target = component;
                msg.action = "replicate_collect=" + std::to_string(replicate_task[(component)]);
                adapt.publish(msg);
            } else {
                //freq[component] += (error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error); 
                //double new_freq = freq[component] + ((error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error));
                double new_freq = freq[component] + ((kp[component]/100) * error);
                if(new_freq >= 0.1 && new_freq <= 40) {
                    freq[component] = new_freq;
                    archlib::AdaptationCommand msg;
                    msg.source = ros::this_node::getName();
                    msg.target = component;
                    msg.action = "freq=" + std::to_string(freq[component]);
                    adapt.publish(msg);
                }
            }
        }
    } else {
        exception_buffer[component] = (exception_buffer[component] > 0) ? 0 : exception_buffer[component] - 1;
    }

    if(exception_buffer[component]>4){
        archlib::Exception msg;
        msg.source = ros::this_node::getName();
        msg.target = "/engine";
        msg.content = component+"=1";
        except.publish(msg);
        exception_buffer[component] = 0;
    } else if (exception_buffer[component]<-4) {
        archlib::Exception msg;
        msg.source = ros::this_node::getName();
        msg.target = "/engine";
        msg.content = component+"=-1";
        except.publish(msg);
        exception_buffer[component] = 0;
    }
    
    invocations[component].clear();
}

int main(){double ref,cur;while(std::cin>>ref>>cur){Controller c;std::string k="/g3t1_1";c.r_ref[k]=ref;c.r_curr[k]=cur;c.kp[k]=50;c.freq[k]=10;c.apply_reli_strategy(k);std::cout<<std::setprecision(17)<<c.freq[k]<<" "<<c.adapt.actions.size();for(auto a:c.adapt.actions)std::cout<<" "<<a;std::cout<<"\n";}}
