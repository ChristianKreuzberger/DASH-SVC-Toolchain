#include "parse.h"

#include <iostream>
using namespace std;


using namespace dash;
using namespace dash::network;



std::vector<std::string> GetSVCSegmentURLs(const char* url, const char* layer_id)
{
  cerr << "Opening " << url << endl;
  // do nothing
  dash::mpd::IMPD *mpd;
  dash::IDASHManager *manager;
  manager = CreateDashManager();
  mpd = manager->Open ((char*)url);

  std::vector<std::string> segmentList;



  if (mpd == NULL)
    {
      cerr << "Error opening mpd..." << endl;
      return segmentList;
    }

  cerr << "Successfully opened MPD!" << endl;

  std::vector<std::string> locs = mpd->GetLocations();

  cerr << "Received " << locs.size() << " locations: " << endl;

  for (int i = 0; i < locs.size (); i++)
    {
      cerr << locs[i] << endl;
    }


  cerr << mpd->GetMPDPathBaseUrl ()->GetUrl () << endl;

  std::vector<dash::mpd::IPeriod *> periods = mpd->GetPeriods ();

  if(periods.size() == 0)
    {
      cerr << "No periods found in MPD..." << endl;
      return segmentList;
    }

  cerr << "Found " << periods.size() << " periods in MPD" << endl;


  dash::mpd::IPeriod* per = periods.at(0);
  std::vector<dash::mpd::IBaseUrl*> baseUrls = per->GetBaseURLs();



  std::string base_url = "";

  if (baseUrls.size() > 0)
  {
    cerr << "Received " << baseUrls.size() << " base URLs: " << endl;

    for (int i = 0; i < baseUrls.size (); i++)
    {
      cerr << baseUrls[i] << endl;
    }
    } else {

      base_url = mpd->GetBaseUrls ().at(0)->GetUrl();
    }
    cerr << "BASE URL:" << base_url << endl;


    // get adaptation sets
    std::vector<dash::mpd::IAdaptationSet*> sets = per->GetAdaptationSets ();
    dash::mpd::IAdaptationSet* set = sets.at (0); //Todo deal with different sets

    cerr << "Sets.size() = " << sets.size() << endl; 


    std::string initSegment = base_url + set->GetSegmentBase ()->GetInitialization ()->GetSourceURL ();

    cerr << "Download Init Segment:" << initSegment << endl;

    std::vector<dash::mpd::IRepresentation*> reps = set->GetRepresentation ();

    int width, height;
    dash::mpd::IRepresentation* rep;



  segmentList.push_back (initSegment);

  // iterate over all representations
  for(size_t j = 0; j < reps.size(); j++)
  {
    cerr << "--------------------" << endl;
    rep = reps.at(j);
    
    width = rep->GetWidth();
    height = rep->GetHeight();

    std::vector<dash::mpd::ISegmentURL*> segmentUrls = rep->GetSegmentList ()->GetSegmentURLs();
    cerr << "Representation ID: " << rep->GetId () << endl;
    std::vector<std::string> dependencies = rep->GetDependencyId ();

    if (dependencies.size () > 0)
    {
      cerr << "Dependency ID: " << dependencies.at(0) << endl;
    }

    std::vector<std::string> codecs = rep->GetCodecs ();

    if (codecs.size() > 0)
    {
      cerr << "Codec: " << codecs.at(0) << endl;
    }


    cerr << "WxH: " << width << "x" << height << ", BW:" << rep->GetBandwidth () << endl;
    cerr << "Segment Duration (Frames): " << rep->GetSegmentList()->GetDuration() << endl;

    cerr << "FramesPerSecond: " << rep->GetFrameRate () << endl;

    cerr << "Number of segments: " << segmentUrls.size () << endl;
      
    if (layer_id == NULL || (layer_id != NULL && rep->GetId().compare(layer_id) == 0))
    {
	for (int k = 0; k < segmentUrls.size(); k++)
	{

	    // download
	    string newURL = base_url;
	    newURL += segmentUrls.at(k)->GetMediaURI();

	    if (k+1 >= segmentList.size())
	    {
	      segmentList.push_back (newURL);
	    }
	    else
	     {
	      segmentList[k+1] += "," + newURL;
	      }

	   // cerr << "Download " << newURL << endl;
	}
    } else {
   		cerr << "Skipping this layer..." << endl;
    }


  }


  return segmentList;


}
