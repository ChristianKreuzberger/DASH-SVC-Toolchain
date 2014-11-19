#include <iostream>
#include "parse.h"

using namespace std;

#define DEMO_MPD_URL "http://concert.itec.aau.at/SVCDataset/dataset/mpd/factory-I-720p.mpd"




int main(int argc, const char* argv[])
{
  std::vector<std::string> URLs;
  if (argc == 1)
  {
    URLs = GetSVCSegmentURLs(DEMO_MPD_URL);
  } else if (argc == 2)
  {
    URLs = GetSVCSegmentURLs(argv[1]);
  }
  else
  {
    cerr << "Too many parameters supplied. Expected only one parameter: MPD file." << endl;
    return -1;
  }

  for( std::vector<std::string>::const_iterator i = URLs.begin(); i != URLs.end(); ++i)
    std::cout << *i << endl;

}
