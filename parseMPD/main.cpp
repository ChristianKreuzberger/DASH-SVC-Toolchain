#include <iostream>
#include "parse.h"

using namespace std;

#define DEMO_MPD_URL "http://concert.itec.aau.at/SVCDataset/dataset/mpd/factory-I-720p.mpd"



/***
  Parameters for commandline:
  parseMPD [MPD_URL] [LAYER_ID]
*/
int main(int argc, const char* argv[])
{
  std::vector<std::string> URLs;
  if (argc == 1)
  {
    cerr << "Parsing " << DEMO_MPD_URL << " - no layer restriction" << endl;
    URLs = GetSVCSegmentURLs(DEMO_MPD_URL, NULL);
  } else if (argc == 2)
  {
    cerr << "Parsing " << argv[1] << " - no layer restriction" << endl;
    URLs = GetSVCSegmentURLs(argv[1], NULL);
  } else if (argc == 3)
  {
    cerr << "Parsing " << argv[1] << " - Layer: " << argv[2] << endl;
    URLs = GetSVCSegmentURLs(argv[1], argv[2]);   
  }
  else
  {
    cerr << "Wrong number of parameters supplied. Syntax: " << argv[0] << " [MPD_URL] [LAYER_ID] " << endl;
    return -1;
  }

  for( std::vector<std::string>::const_iterator i = URLs.begin(); i != URLs.end(); ++i)
    std::cout << *i << endl;

}
