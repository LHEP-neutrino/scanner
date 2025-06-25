
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>


#define CN 64
#define startch 26
#define endch 31
#define startMon 12
#define endMon 13
#define sn 175780172

//Can be used do give some outputs
bool debug = 0;
// make sure that you select the right gain
//Float_t gain[] = {745.71,703.27,699.83,749.79,799.54,749.81};
//Float_t gain[] ={162.42,303,291.56,316.03,287.57,303.07};
Float_t gain[] ={334.61,586.2,559.51,251.31,399.81,334.61};//gain4
int numb_of_meas = 4; //number of measurements that one wants to plot the histogram of the integral
//Float_t mon_gain[]= {749.81,799.76};
//Float_t mon_gain[] = {360.75,319.77};
Float_t mon_gain[] = {640.98,346.01};//gain4


//path of the data
TString data_path = {"/data/3dscan/root_files/"};


//Sum of an array
Float_t arr_sum(Float_t arr[], int n)
{
    Float_t  sum = 0; // initialize sum
 
    // Iterate through all elements
    // and add them to sum
    for (int i = 0; i < n; i++)
    sum += arr[i];
 
    return sum;
}

void Printer_stab_conv(const char* logfilename){
	Float_t x,y,z;
	char filename[30];		
	Float_t LY_adc[endch-startch+1];
	Float_t LY_nph[endch-startch+1];
        Float_t LY_mon_adc[2];
        Float_t LY_mon_nph[2];

	Float_t LY_adc_rms[endch-startch+1];
	Float_t LY_nph_rms[endch-startch+1];
	Float_t LY_adc_rms_squ[endch-startch+1];
	Float_t LY_nph_rms_squ[endch-startch+1];
        Float_t LY_mon_adc_rms[2];
        Float_t LY_mon_nph_rms[2];
        Float_t LY_mon_adc_rms_squ[2];
        Float_t LY_mon_nph_rms_squ[2];

	Float_t LY_tot_adc;
	Float_t LY_tot_nph;	
	Float_t LY_tot_mon_adc;
	Float_t LY_tot_mon_nph;

	Float_t LY_tot_adc_rms;
	Float_t LY_tot_nph_rms;	
	Float_t LY_tot_mon_adc_rms;
	Float_t LY_tot_mon_nph_rms;
	
	FILE *f_in; 
	if((f_in = fopen(logfilename,"r"))==NULL){
		fprintf( stderr, "Error- Unable to open %s\n", logfilename);
		exit(-1);
	}
	printf("Open %s\n",logfilename);
	
	
	string scan_name = string(logfilename).substr(0,string(logfilename).size()-4);
	//cout<<scan_name;
	string out_filename = scan_name + string("_stabConv") + string(".root");
	
	TFile* f_out = new TFile(out_filename.c_str(),"RECREATE");
	TTree *t_out = new TTree("t_out","t_out");
	t_out->Branch("x",&x);
	t_out->Branch("y",&y);
	t_out->Branch("z",&z);	
	t_out->Branch("LY_adc",&LY_adc,"LY_adc[6]/F");
	t_out->Branch("LY_adc_rms",&LY_adc_rms,"LY_adc_rms[6]/F");	
	t_out->Branch("LY_nph",&LY_nph,"LY_nph[6]/F");
	t_out->Branch("LY_nph_rms",&LY_nph_rms,"LY_nph_rms[6]/F");
        t_out->Branch("LY_mon_adc",&LY_mon_adc,"LY_mon_adc[2]/F");
      	t_out->Branch("LY_mon_adc_rms",&LY_mon_adc_rms,"LY_mon_adc_rms[2]/F");	
        t_out->Branch("LY_mon_nph",&LY_mon_nph,"LY_mon_nph[2]/F");
	t_out->Branch("LY_mon_nph_rms",&LY_mon_nph_rms,"LY_mon_nph_rms[2]/F");	
	t_out->Branch("LY_tot_adc",&LY_tot_adc);	
	t_out->Branch("LY_tot_nph",&LY_tot_nph);
	t_out->Branch("LY_tot_mon_adc",&LY_tot_mon_adc);	
	t_out->Branch("LY_tot_mon_nph",&LY_tot_mon_nph);
	t_out->Branch("LY_tot_adc_rms",&LY_tot_adc_rms);	
	t_out->Branch("LY_tot_nph_rms",&LY_tot_nph_rms);
	t_out->Branch("LY_tot_mon_adc_rms",&LY_tot_mon_adc_rms);	
	t_out->Branch("LY_tot_mon_nph_rms",&LY_tot_mon_nph_rms);



	//Hist of the Integral
	TCanvas* h = new TCanvas("h","Integral");
	h->DivideSquare((endch-startch)*numb_of_meas,0.01,0.01,0);
	//printf("number of measurements: %d",numb_of_meas);
	int number_of_h=0; //counts through the position of the histograms


	//Hist of the Integral
	TCanvas* h_mon = new TCanvas("h_mon","Integral Monitoring");
	h_mon->DivideSquare((endMon-startMon)*numb_of_meas,0.01,0.01,0);
	//printf("number of measurements: %d",numb_of_meas);
	int number_of_h_mon=0; //counts through the position of the histograms

	//start of the read out, saving and plotting	
	char buffer[256];
	while(fgets(buffer,256,f_in)){
		sscanf(buffer,"%f %f %f %s",&x,&y,&z,filename);
		printf("x: %f y: %f z: %f fn:%s\n",x,y,z,filename);

		//you need a folder with the samename as the log file with a folder that is named "root_files" and there are all the .root files from this log
		TFile *f_light = new TFile(data_path + TString(scan_name) + TString("/rlog_")+ TString(filename) + TString(".root"),"READ");
		if(f_light==0){
			fprintf(stderr,"Error- Data file %s not found\n",filename);
			exit(-1);
		}
		TTree *tr = (TTree*)f_light->Get("rlog");
	
		//tr->Print();	
		
		for(int ch = 0; ch<(endch-startch+1); ch++){
			//Calculates the mean of the integrals and safes them in the Tree	
		        Double_t max_bin = tr->GetMaximum(Form("integral.ch%02d",ch+startch)); 
			TH1F* h_test = new TH1F(Form("h_test%d",ch),"Titel",1000,0,max_bin);
			tr->Project(Form("h_test%d",ch),Form("integral.ch%02d",ch+startch));	
			TH1F *h_temp = (TH1F*)gDirectory->Get(Form("h_test%d",ch));
			
			//from write integral:
                        //tr->Draw(Form("integral.ch%02d>>h_temp(10000,0,max_bin)",ch+startch),Form("sn == %d",sn)); 
                        //TH1F *h_temp = (TH1F*)gDirectory->Get("h_temp");

			LY_adc[ch] = h_temp->GetMean();
			LY_adc_rms[ch] = h_temp -> GetRMS()/sqrt(h_temp->GetEntries());
			//if(debug) printf("%f\n",LY_adc[ch]);
			LY_nph[ch] = LY_adc[ch]/gain[ch];
			LY_nph_rms[ch] = LY_adc_rms[ch]/gain[ch];

			LY_adc_rms_squ[ch]=LY_adc_rms[ch]*LY_adc_rms[ch];
			LY_nph_rms_squ[ch]=LY_nph_rms[ch]*LY_nph_rms[ch];
			
			//Does safe the hist at different locations so that they are all drawn at the end in one Canvas
			tr->Project(Form("h_temp%02d",ch),Form("integral.ch%02d",ch+startch));
			TH1F *h_temp_all = (TH1F*)gDirectory->Get(Form("h_temp%02d",ch));
			h->cd(number_of_h+1);
			h_temp_all->Draw();
			number_of_h=number_of_h+1;

		}
		
		LY_tot_adc = arr_sum(LY_adc,endch-startch+1);
		LY_tot_nph = arr_sum(LY_nph,endch-startch+1);
		
		LY_tot_adc_rms = sqrt(arr_sum(LY_adc_rms_squ,endch-startch+1));
		LY_tot_nph_rms = sqrt(arr_sum(LY_nph_rms_squ,endch-startch+1));

		//monitoring	
                if(z<0){

                        for(int ch = 0; ch<(endMon-startMon)+1; ch++){
				//Calculates the mean of the integrals and safes them in the Tree	
				//tr->Project("h_temp2",Form("integral.ch%02d",ch+startch));	
				//TH1F *h_temp2 = (TH1F*)gDirectory->Get("h_temp2");
				
				
				//Calculates the mean of the integrals and safes them in the Tree	
			        Double_t max_bin = tr->GetMaximum(Form("integral.ch%02d",ch+startMon)); 
				TH1F* h_t_mon = new TH1F(Form("h_t_mon%d",ch),"Titel",1000,0,max_bin);
				tr->Project(Form("h_t_mon%d",ch),Form("integral.ch%02d",ch+startMon));	
				TH1F *h_temp2 = (TH1F*)gDirectory->Get(Form("h_t_mon%d",ch));
				
				LY_mon_adc[ch] = h_temp2->GetMean();
				LY_mon_adc_rms[ch] = h_temp2 -> GetRMS()/sqrt(h_temp2->GetEntries());
				//if(debug) printf("%f\n",LY_adc[ch]);
				LY_mon_nph[ch] = LY_mon_adc[ch]/mon_gain[ch];
				LY_mon_nph_rms[ch] = LY_mon_adc_rms[ch]/mon_gain[ch];
				
				LY_mon_adc_rms_squ[ch] = LY_mon_adc_rms[ch]*LY_mon_adc_rms[ch];
				LY_mon_nph_rms_squ[ch] = LY_mon_nph_rms[ch]*LY_mon_nph_rms[ch];


				//Does safe the hist at different locations so that they are all drawn at the end in one Canvas
				tr->Project(Form("h_temp_mon%02d",ch),Form("integral.ch%02d",ch+startMon));
				TH1F *h_temp_all_mon = (TH1F*)gDirectory->Get(Form("h_temp_mon%02d",ch));
				h_mon->cd(number_of_h_mon+1);
				h_temp_all_mon->Draw();
				number_of_h_mon=number_of_h_mon+1;

			}
			//from old one:
        	                //Double_t max_bin_mon = tr->GetMaximum(Form("integral.ch%02d>>h_temp2",ch));
                	        //tr->Draw(Form("integral.ch%02d>>h_temp2(10000,0,max_bin)",ch),Form("sn == %d",sn));
				//tr->Project("h_temp2",Form("integral.ch%02d",ch));
                	        //TH1F *h_temp2 = (TH1F*)gDirectory->Get("h_temp2");
                	        //LY_mon_adc[ch-startMon] = h_temp2->GetMean();
				//LY_mon_adc_rms[ch] = h_temp2 -> GetRMS();
                	        //if(debug) printf("%f\n",LY_adc[ch]);
                       		//LY_mon_nph[ch-startMon] = LY_mon_adc[ch-startMon]/mon_gain[ch-startMon];
				//LY_mon_nph_rms[ch-startMon] = LY_mon_adc_rms[ch-startMon]/mon_gain[ch-startMon];

	                LY_tot_mon_adc = arr_sum(LY_mon_adc,2);
	        	LY_tot_mon_nph = arr_sum(LY_mon_nph,2);
	
			LY_tot_mon_adc_rms = sqrt(arr_sum(LY_mon_adc_rms_squ,endMon-startMon+1));
			LY_tot_mon_nph_rms = sqrt(arr_sum(LY_mon_nph_rms_squ,endMon-startMon+1));
                }
		
		else{
			LY_mon_adc[0]=0;
			LY_mon_adc[1]=0;
			LY_mon_nph[0]=0;	
			LY_mon_nph[1]=0;	
	                LY_tot_mon_adc = arr_sum(LY_mon_adc,2);
	                LY_tot_mon_nph = arr_sum(LY_mon_nph,2);
			
			LY_mon_adc_rms[0]=0;
			LY_mon_adc_rms[1]=0;
			LY_mon_nph_rms[0]=0;	
			LY_mon_nph_rms[1]=0;	
			LY_mon_adc_rms_squ[0]=0;
			LY_mon_adc_rms_squ[1]=0;
			LY_mon_nph_rms_squ[0]=0;	
			LY_mon_nph_rms_squ[1]=0;	
			LY_tot_mon_adc_rms = sqrt(arr_sum(LY_mon_adc_rms_squ,endMon-startMon+1));
			LY_tot_mon_nph_rms = sqrt(arr_sum(LY_mon_nph_rms_squ,endMon-startMon+1));
		}
	
		f_out->cd();
		t_out->Fill();
	}
	t_out->Write("t_out",TObject::kOverwrite);
	f_out->Close();
}
