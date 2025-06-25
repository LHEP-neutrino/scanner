#include "tile_plot_new_setup2.h"
//files for 2 cm steps only
//LCM - good
//const char* files[]={"FLCM_01_02_03_2_stabConv.root","FLCM_04_05_06_2_2_stabConv.root","FLCM_07_08_09_2_1_stabConv.root","FLCM_13_14_15_2_1_stabConv.root","FLCM_16_17_18_2_1_stabConv.root",\
"FLCM_19_20_21_2_1_stabConv.root","FLCM_22_23_24_2_1_stabConv.root","FLCM_25_26_27_2_4_stabConv.root"};


//all scans - not used
//const char* files[]={"FACL_4p21_2_8_stabConv.root","FACL_4p21_2_9_stabConv.root","FACL_4p07_2_1_stabConv.root","FACL_4p09_2_1_stabConv.root","FACL_4p05_2_1_stabConv.root",\
"FACL_4p05_2_3_stabConv.root","FACL_4p05_2_4_stabConv.root","FACL_4p19_2_1_stabConv.root","FACL_4p19_2_2_stabConv.root","FACL_4p14_2_1_stabConv.root","FACL_4p14_2_2_stabConv.root",\
"FACL_4p15_2_1_stabConv.root","FACL_4p15_2_2_stabConv.root","FACL_4p17_2_1_stabConv.root","FACL_4p18_2_1_stabConv.root","FACL_4p04_2_1_stabConv.root",\
"FACL_4p08_2_1_stabConv.root","FACL_4p20_2_1_stabConv.root","FACL_4p02_2_1_stabConv.root","FACL_4p16_2_1_stabConv.root","FACL_4p12_2_1_stabConv.root",\
"FACL_4p22_2_3_stabConv.root","FACL_4p23_2_1_stabConv.root","FACL_4p29_2_1_stabConv.root","FACL_4p27_2_1_stabConv.root","FACL_4p00_2_1_stabConv.root",\
"FACL_4p06_2_1_stabConv.root","FACL_4p11_2_1_stabConv.root","FACL_4p24_2_1_stabConv.root","FACL_4p29_2_2_stabConv.root","FACL_4p18_2_2_stabConv.root","FACL_4p07_2_2_stabConv.root",\
"FACL_4p20_2_2_stabConv.root","FACL_4p09_2_3_stabConv.root","FACL_4p17_2_2_stabConv.root","FACL_4p08_2_2_stabConv.root","FACL_4p18_2_3_stabConv.root","FACL_4p16_2_2_stabConv.root",\
"FACL_4p02_2_2_stabConv.root","FACL_4p04_2_2_stabConv.root","FACL_4p00_2_2_stabConv.root","FACL_4p22_2_6_stabConv.root","FACL_4p23_2_3_stabConv.root","FACL_4p24_2_4_stabConv.root",\
"FACL_4p27_2_4_stabConv.root","FACL_4p06_2_3_stabConv.root","FACL_4p11_2_3_stabConv.root","FACL_4p12_2_3_stabConv.root"};

//without foil on edge - good
const char* files[]={"FACL_4p21_2_8_stabConv.root","FACL_4p01_2_1_stabConv.root","FACL_4p04_2_1_stabConv.root","FACL_4p02_2_1_stabConv.root",\
"FACL_4p13_2_1_stabConv.root","FACL_4p27_2_1_stabConv.root","FACL_4p11_2_1_stabConv.root","FACL_4p14_2_1_stabConv.root",\
"FACL_4p19_2_1_stabConv.root","FACL_4p24_2_1_stabConv.root","FACL_4p08_2_1_stabConv.root","FACL_4p22_2_3_stabConv.root",\
"FACL_4p06_2_1_stabConv.root","FACL_4p18_2_2_stabConv.root",\
"FACL_4p23_2_1_stabConv.root","FACL_4p05_2_1_stabConv.root","FACL_4p17_2_1_stabConv.root","FACL_4p00_2_1_stabConv.root",\
"FACL_4p20_2_1_stabConv.root","FACL_4p16_2_1_stabConv.root","FACL_4p29_2_2_stabConv.root",\
	"TBB_Foil_W_o_mirror_2_1_stabConv.root","TBB_Foil_W_o_mirror_2_2_stabConv.root",\
"TBB_Foil_W_o_mirror_2_3_stabConv.root", "TBB_Foil_W_o_mirror_2_4_stabConv.root", "TBB_Foil_W_o_mirror_2_5_stabConv.root", "TPB_Foil_w_mirror_2_2_stabConv.root","TPB_Foil_w_mirror_2_3_stabConv.root","TPB_Foil_w_mirror_2_4_stabConv.root"}; 
//could be added but is in it ,"FACL_4p20_2_2_stabConv.root"; could be added but has not a perfect scan FACL_4p15_2_1_stabConv.root

//with dichroic mirror on edge - good
//const char* files[]={"FACL_4p01_2_2_stabConv.root","FACL_4p04_2_2_stabConv.root","FACL_4p21_2_9_stabConv.root","FACL_4p09_2_1_stabConv.root",\
	"FACL_4p02_2_2_stabConv.root","FACL_4p13_2_2_stabConv.root","FACL_4p20_2_5_stabConv.root",\
	"FACL_4p07_2_1_stabConv.root","FACL_4p27_2_4_stabConv.root","FACL_4p11_2_3_stabConv.root","FACL_4p19_2_2_stabConv.root","FACL_4p14_2_2_stabConv.root",\
	"FACL_4p24_2_4_stabConv.root","FACL_4p15_2_2_stabConv.root","FACL_4p08_2_2_stabConv.root","FACL_4p18_2_3_stabConv.root","FACL_4p22_2_6_stabConv.root",\
	"FACL_4p06_2_3_stabConv.root","FACL_4p23_2_3_stabConv.root","FACL_4p05_2_3_stabConv.root",\
	"FACL_4p12_2_3_stabConv.root","FACL_4p17_2_2_stabConv.root","FACL_4p00_2_2_stabConv.root","FACL_4p16_2_2_stabConv.root"}; 
	//doubel: "FACL_4p12_2_1_stabConv.root", "FACL_4p09_2_3_stabConv.root",

//before and after coldtest: - good
//const char* files[]= {"FACL_4p05_2_3_stabConv.root","FACL_4p05_2_4_stabConv.root"}; //_3 is before

//with different mirrors: edge mirrors: no, dichroic, normal (total) [no back mirror], (dichoic in the end again) -- good
//const char* files[]={"FACL_4p01_2_1_stabConv.root", "FACL_4p01_2_2_stabConv.root", "FACL_4p01_2_3_stabConv.root", "FACL_4p01_2_6_stabConv.root"};
//const char* files[]={"FACL_4p19_2_1_stabConv.root", "FACL_4p19_2_2_stabConv.root", "FACL_4p19_2_4_stabConv.root", "FACL_4p19_2_6_stabConv.root"};
//const char* files[]={"FACL_4p24_2_1_stabConv.root", "FACL_4p24_2_4_stabConv.root", "FACL_4p24_2_5_stabConv.root", "FACL_4p24_2_7_stabConv.root"};

//with different mirrors: edge mirrors: dichroic, normal (total) [no back mirror], (dichoic in the end again) -- good
//const char* files[]={"FACL_4p15_2_2_stabConv.root", "FACL_4p15_2_5_stabConv.root", "FACL_4p15_2_7_stabConv.root"};


//with different back mirrors: normal edge [no back mirror],  normal edge [dichoric back mirror], normal edge [normal back mirror] -- good
//const char* files[]={"FACL_4p01_2_3_stabConv.root", "FACL_4p01_2_5_stabConv.root", "FACL_4p01_2_4_stabConv.root"};

//with different back mirrors: normal edge [no back mirror], normal edge [normal back mirror] -- good
//const char* files[]={"FACL_4p19_2_4_stabConv.root", "FACL_4p19_2_5_stabConv.root"};
//const char* files[]={"FACL_4p24_2_5_stabConv.root", "FACL_4p24_2_6_stabConv.root"};
//const char* files[]={"FACL_4p15_2_5_stabConv.root", "FACL_4p15_2_6_stabConv.root"};

//stability of the scans (all the same) -- good
//const char* files[]={"FACL_4p15_2_7_stabConv.root","FACL_4p15_2_8_stabConv.root","FACL_4p15_2_9_stabConv.root"};

//compare impact of spacer: without mirror, with mirror, (with mirror again if available):
//const char* files[]={"FACL_4p15_2_10_stabConv.root","FACL_4p15_2_11_stabConv.root","FACL_4p15_2_12_stabConv.root"};
//const char* files[]={"FACL_4p19_2_8_stabConv.root","FACL_4p19_2_7_stabConv.root"};
//const char* files[]={"FACL_4p02_2_3_stabConv.root","FACL_4p02_2_4_stabConv.root"};

//compare same LCM for different Light seetings - good 90, 120, 150, 180
//const char* files[]={"FLCM_13_14_15_2_1_stabConv.root","FLCM_13_14_15_2_2_stabConv.root","FLCM_13_14_15_2_3_stabConv.root","FLCM_13_14_15_2_4_stabConv.root"};

//compare same ACL for different Light seetings - good 90, 120, 150, 180, 255
//const char* files[]={"FACL_4p04_2_3_stabConv.root","FACL_4p04_2_4_stabConv.root","FACL_4p04_2_5_stabConv.root",\
"FACL_4p04_2_6_stabConv.root","FACL_4p04_2_2_stabConv.root"};


//compare LCM vs ACL directly - good (check 4p19)
//const char* files[]={"FACL_4p04_2_3_stabConv.root","FACL_4p15_2_4_stabConv.root","FACL_4p06_2_4_stabConv.root","FACL_4p19_2_3_stabConv.root",\
"FACL_4p11_2_6_stabConv.root",\
"FLCM_13_14_15_2_1_stabConv.root","FLCM_16_17_18_2_1_stabConv.root",\
"FLCM_19_20_21_2_1_stabConv.root","FLCM_25_26_27_2_4_stabConv.root"}; //90s
//const char* files[]={"FACL_4p04_2_4_stabConv.root","FLCM_13_14_15_2_2_stabConv.root"}; //120s
//const char* files[]={"FACL_4p04_2_5_stabConv.root","FLCM_13_14_15_2_3_stabConv.root"}; //150s
//const char* files[]={"FACL_4p04_2_6_stabConv.root","FLCM_13_14_15_2_4_stabConv.root"}; //180s

//for comparison before hardware upgrade and after: (after FSDI)
//const char* files[]={"FACL_4p12_2_3_stabConv.root", "FACL2_4p_12_2_1_stabConv.root", "FACL2_4p12_2_2_stabConv.root", "FACL2_4p12_2_3_stabConv.root","FACL2_4p16_2_1_stabConv.root"};

//Fretligh foil:
//const char* files[]={"FACL_4p21_2_8_stabConv.root"};//"Fret_6p_V1_1_stabConv.root","Fret_6p_V2_1_stabConv.root","Fret_6p_V3_1_stabConv.root","Fret_0p_V1_1_stabConv.root","Fret_0p_V2_1_stabConv.root"};

//for single once
//const char* files[]={"Fret_plastic_w_o_foil_1_stabConv.root","Fret_plastic_w_dichroic_foil_stabConv.root","Fret_plastic_w_blaze_foil_1_stabConv.root"};
float C[2];

float *getMean(const char* rootfilename){
	//get the mean of the monitoring
	
	TFile* f_in = new TFile(rootfilename,"READ");
	TTree* t_out = (TTree*)f_in->Get("t_out");
	
	//Make linear fit
	//Plot the drift on the monitor per step
	TCanvas* mon_drift_s = new TCanvas("mon_drift_s","Mean",600,300);
	mon_drift_s->cd();
	t_out->Draw("LY_tot_mon_nph:Entry$>>h_temp2");
	C[0] = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //get the mean
	float stdDev = TMath::RMS(t_out->GetSelectedRows(),t_out->GetV1()); //get the std deviation
	C[1] = stdDev/sqrt(t_out->GetSelectedRows()); //calculate the error
	mon_drift_s->Destructor();
	return C;
}

float *getMeanLRS(const char* rootfilename){
        //get the mean of the LRS

        TFile* f_in = new TFile(rootfilename,"READ");
        TTree* t_out = (TTree*)f_in->Get("t_out");

        //Make linear fit
        //Plot the drift per step
        TCanvas* drift_s = new TCanvas("drift_s","Mean",600,300);
        drift_s->cd();
        t_out->Draw("LY_tot_nph:Entry$>>h_temp2");
        C[0] = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //get the mean
        float stdDev = TMath::RMS(t_out->GetSelectedRows(),t_out->GetV1()); //get the std deviation
        C[1] = stdDev/sqrt(t_out->GetSelectedRows()); //calculate the error
        drift_s->Destructor();
        return C;
}



void plots_new_setup2(){
	const int size_of_files=sizeof(files)/sizeof(files[0]);
	float_t means[size_of_files];
	float_t errors[size_of_files];
	float_t scan_nr[size_of_files];
	
	TString strFullpath = TString("/home/lhep/ArCLight_3DScan/scan_ACLFSD_1/scan_plots_new_setup2/");
	
	
	//Create canvas and pave box
	TCanvas* means_monitoring = new TCanvas("means_monitoring","monitoring mean for different tiles",3000,1500);
	means_monitoring->cd();
	//means_monitoring->DivideSquare(2,0.1,0.1,0);
	//TPaveText *pt = new TPaveText(0.1,0.1,0.9,0.9);
	
	Float_t* K;
	//plot the different means of monitoring
	for(int i=0;i<size_of_files;i++){
		K = getMean(files[i]);
		means[i] = K[0];
		errors[i] = K[1];
		scan_nr[i]=i;
		//printf("calc: %f \n",getMean(files[i]));
		//printf("error: %f \n",errors[i]);
		//printf("means: %f \n",means[i]);
		//printf("step: %f \n",scan_nr[i]);
		//pt->AddText(Form("Nr. %d is %s",i,files[i]));
	}

	TGraphErrors* gr_monitor = new TGraphErrors(size_of_files,scan_nr,means,0,errors);
	gr_monitor->SetMarkerStyle(20);
	gr_monitor->SetTitle("Means of the monitoring for different Tiles;;LY mean");
	means_monitoring->cd();
	gr_monitor->GetXaxis()->SetLimits(-1,size_of_files);
	gPad->SetLeftMargin(0.15);
	gPad->SetBottomMargin(0.2);

	//set the bin labeling
	const char* label[size_of_files];
 	for(int k=0;k<size_of_files;k++){
                string scan_name = string(files[k]).substr(0,string(files[k]).size()-14);
                //cout<<("Scan_name: "+string(scan_name)+string("\n"));
                label[k]=scan_name.c_str();
                gr_monitor->GetXaxis()->SetBinLabel(gr_monitor->GetXaxis()->FindBin(k),label[k]);
        }
	gr_monitor->Draw("ap"); 
	//means_monitoring->cd(2);
	//pt->Draw();
	means_monitoring->SaveAs(TString(strFullpath)+TString("means_of_all_tiles")+TString(".png"));


	//calculate the mean of all monitorings
	float mean_all = TMath::Mean(size_of_files,means);
	printf("Total mean is: %f \n",mean_all);
	

	//do a stability test plot if you uncomment:
	/*


	*/


	//plot the tile plots and return the sum and its error
	Float_t *A;
	Float_t sum[size_of_files];
	Float_t sum_error[size_of_files];	
	Float_t fixed_error[size_of_files]; //fixes the error on a value

	ofstream myfile;
	myfile.open("sum_new_setup2.txt");

	for(int i=0;i<size_of_files;i++){
		A=tile_plot(files[i],mean_all);
		sum[i]=A[0];
		sum_error[i]=A[1];
		fixed_error[i]=3000;
		//printf("sum %s: %f \n",files[i],sum[i]);
		//cout<<"error "<<*sum_error<<endl;
		
		myfile << files[i] << ";";
		myfile << sum[i] << ";";
		myfile << sum_error[i] << "; \n";

	}

	//plot the histogram of the sum
	TCanvas* C_sum = new TCanvas("C_sum","Sum of the different tiles in a hist",6000,3000);
	//C_sum->DivideSquare(2,0.1,0.1,0);
	C_sum->cd();
	TGraphErrors* gr_sum = new TGraphErrors(size_of_files,scan_nr,sum,0,sum_error);
	//TGraphErrors* gr_sum = new TGraphErrors(size_of_files,scan_nr,sum,0,fixed_error);
	gr_sum->SetMarkerStyle(20);
	gr_sum->SetTitle("Sum of the total light per tile;;total p.e.");
	gr_sum->GetXaxis()->SetLimits(-1,size_of_files);

	//set the bin labelling
	const char* label2[size_of_files];
	for(int k=0;k<size_of_files;k++){
		string scan_name = string(files[k]).substr(0,string(files[k]).size()-14);
		//cout<<("Scan_name: "+string(scan_name)+string("\n"));
		label2[k]=scan_name.c_str();
		//cout<<label2[k]+string("\n");
		gr_sum->GetXaxis()->SetBinLabel(gr_sum->GetXaxis()->FindBin(k),label2[k]);
	}
	gPad->SetLeftMargin(0.15);
	gPad->SetBottomMargin(0.2);
	gr_sum->GetYaxis()->SetRangeUser(0,30000); //ACL 25000; LCM 50000; s90: 10000
	//gr_sum->GetYaxis()->SetRangeUser(0,5000);
	gr_sum->Draw("ap");
	//C_sum->cd(2);
	//pt->Draw();
	C_sum->SaveAs(TString(strFullpath)+TString("Sum_of_total_photons_all_tiles")+TString(".png"));

	myfile.close();
} 
