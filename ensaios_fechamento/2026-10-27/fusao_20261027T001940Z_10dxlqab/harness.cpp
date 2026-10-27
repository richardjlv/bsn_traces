#include "libbsn/processor/Processor.hpp"
#include <iomanip>
int main(){std::vector<double> v(6);while(std::cin>>v[0]>>v[1]>>v[2]>>v[3]>>v[4]>>v[5])std::cout<<std::setprecision(17)<<bsn::processor::data_fuse(v)<<"\n";}
