#include "tile_plot_new_setup1.h"
//const char* files[]={"FACL_4p04_h_2_stabConv.root"};
const char* files[]={"LCM_high_res_2_stabConv.root"};

//1cm files only:
//const char* files[]={""};
float C[2];

float *getMean(const char* rootfilename){
	//get the mean of the monitoring
	
	TFile* f_in = new TFile(rootfilename,"READ");
	TTree* t_out = (TTree*)f_in->Get("t_out");
	
	//Make linear fit
	//Plot the drift on the monitor per step
	TCanvas* mon_drift_s = new TCanvas("mon_drift_s","Mean",3000,1500);
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
        TCanvas* drift_s = new TCanvas("drift_s","Mean",3000,1500);
        drift_s->cd();
        t_out->Draw("LY_tot_nph:Entry$>>h_temp2");
        C[0] = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //get the mean
        float stdDev = TMath::RMS(t_out->GetSelectedRows(),t_out->GetV1()); //get the std deviation
        C[1] = stdDev/sqrt(t_out->GetSelectedRows()); //calculate the error
        drift_s->Destructor();
        return C;
}



void plots_new_setup1(){
	const int size_of_files=sizeof(files)/sizeof(files[0]);
	float_t means[size_of_files];
	float_t errors[size_of_files];
	float_t scan_nr[size_of_files];
	
	TString strFullpath = TString("/home/lhep/ArCLight_3DScan/scan_ACLFSD_1/scan_plots_new_setup1/");
	
	
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
	myfile.open("sum_new_setup1.txt");

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
	TCanvas* C_sum = new TCanvas("C_sum","Sum of the different tiles in a hist",3000,1500);
	//C_sum->DivideSquare(2,0.1,0.1,0);
	C_sum->cd();
	TGraphErrors* gr_sum = new TGraphErrors(size_of_files,scan_nr,sum,0,sum_error);
	//TGraphErrors* gr_sum = new TGraphErrors(size_of_files,scan_nr,sum,0,fixed_error);
	gr_sum->SetMarkerStyle(20);
	gr_sum->SetTitle("Sum of the total light per tile;;total photoelectrons");
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
	gr_sum->GetYaxis()->SetRangeUser(0,200000);
	//gr_sum->GetYaxis()->SetRangeUser(0,5000);
	gr_sum->Draw("ap");
	//C_sum->cd(2);
	//pt->Draw();
	C_sum->SaveAs(TString(strFullpath)+TString("Sum_of_total_photons_all_tiles")+TString(".png"));

	myfile.close();
} 
