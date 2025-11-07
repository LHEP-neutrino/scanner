//used in the plots.C file

Float_t sum_and_error[2];
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

Float_t *tile_plot(const char* rootfilename,const float mean_of_all_monitors){
	bool scan_no_cor = false; //scan without correction
	bool mon_only = false; //monitoring points only, not dependent on step
	bool sipm_no_cor = true; //each SiPM individual plotted
	bool correction = true; //monitoring compared to the step, make linear fit and do the scan plot but corrected and corrected SiPm individual
	
	float C; //const to which all the values will be adjusted
	float factor; //this is the correction to put all of the Tiles on the same level
	Float_t sum;
	Float_t sum_error;
	
	
	TFile* f_in = new TFile(rootfilename,"READ");
	TTree* t_out = (TTree*)f_in->Get("t_out");


	TString strFullpath = TString("/home/daq/ArCLight_3DScan/scan_ACL3_series/scan_plots_RnD/")+TString(string(rootfilename).substr(0,string(rootfilename).size()-5))+TString("/");
	
	gSystem->MakeDirectory(strFullpath);

	if(scan_no_cor){
		//Canvas Labeling
		TCanvas* Scan = new TCanvas("Scan"+TString(rootfilename),"Scan plot "+TString(rootfilename),3000,3000);
		Scan->cd();
		
		//create Histogram
		TH2F* h = new TH2F("h"+TString(rootfilename),"3D Scan "+TString(rootfilename), 15,0,300,14,0,280);
		t_out->Project("h"+TString(rootfilename),"y:x","LY_tot_nph*(y<300)"); //y<300 so that the monitor is not shown
		h->SetTitle(Form("Light per point %s;x-position;y-position",rootfilename));
		gStyle->SetOptStat("");
		h->Draw("colz");
		Scan->SaveAs(TString(strFullpath)+TString("scan_no_cor_all_tiles")+TString(".png"));
	}

	if(sipm_no_cor){
		//Canvas Labeling
		TCanvas* Scan_s = new TCanvas("Scan_s"+TString(rootfilename),"Scan plot for each SiPM "+TString(rootfilename),3000,3000);
		Scan_s->DivideSquare(6,0.01,0.01,0);
		Scan_s->cd();

		//create Histogram
		for(int i=0;i<6;i++){
			Scan_s->cd(i+1);
			TH2F* h = new TH2F(Form("h%d",i)+TString(rootfilename),"3D Scan SiPMs "+TString(rootfilename), 15,0,300,14,0,280);
			t_out->Project(Form("h%d",i)+TString(rootfilename),"y:x",Form("LY_nph[%d]*(y<300)",i)); //y<300 so that the monitor is not shown
			h->SetTitle(Form("Light per point for SiPM %d in %s;x-position;y-position",i+1,rootfilename));
			h->Draw("colz");
		}
		Scan_s->SaveAs(TString(strFullpath)+TString("scan_SiPM_no_cor_all_tiles")+TString(".png"));
	}

	if(mon_only){
		//Plot the drift on the monitor
		TCanvas* mon_drift = new TCanvas("mon_drift"+TString(rootfilename),"Drift of the Monitor "+TString(rootfilename),3000,3000);
		mon_drift->cd();
		t_out->Draw(Form("LY_tot_mon_nph:-z>>h_temp%s",rootfilename),"z<0");
		TH1F *h_mon = (TH1F*)gDirectory->Get("h_temp"+TString(rootfilename));
		h_mon->SetMarkerStyle(20);
		h_mon->SetTitle(Form("Drift on the monitor %s;step;number of photons",rootfilename));
		gStyle->SetOptStat("");
		h_mon->Draw();
		mon_drift->SaveAs(TString(strFullpath)+TString("monitor_drift_no_fit_all_tiles")+TString(".png"));
	}

	if(correction){
		//Make linear fit
		//Plot the drift on the monitor per step
		TCanvas* mon_d = new TCanvas("mon_d"+TString(rootfilename),"Drift of the Monitor Linear Fit "+TString(rootfilename),3000,3000);
		mon_d->cd();
		t_out->Draw(Form("LY_tot_mon_nph:Entry$:LY_tot_mon_nph_rms>>h_temp3%s",rootfilename),"z<0&&Entry$!=0");
		//t_out->Draw(Form("LY_tot_mon_nph:Entry$>>h_temp3%s",rootfilename),"z<0&&Entry$!=0&&Entry$!=1");
		TGraphErrors *gr_mon = new TGraphErrors(t_out->GetSelectedRows(),t_out->GetV2(),t_out->GetV1(),0,t_out->GetV3());
		TF1 *fitt = new TF1("fitt"+TString(rootfilename),"[0]*x+[1]",0,t_out->GetEntries());
		gr_mon->Fit("fitt"+TString(rootfilename));
		gr_mon->SetMarkerStyle(20);
		gr_mon->SetTitle(Form("Drift on the monitor corresponding to the step %s;step;number of photons",rootfilename));
		gr_mon->Draw("ap");
		Double_t k = fitt->GetParameter(0);
		Double_t A = fitt->GetParameter(1);

	
	
	
		/*old version:
		//Make linear fit
		//Plot the drift on the monitor per step
		TCanvas* mon_drift_s = new TCanvas("mon_drift_s"+TString(rootfilename),"Drift of the Monitor Linear Fit "+TString(rootfilename),3000,1500);
		mon_drift_s->cd();
		t_out->Draw(Form("LY_tot_mon_nph:Entry$>>h_temp2%s",rootfilename),"z<0&&Entry$!=0");
		TH1F *h_mon_s = (TH1F*)gDirectory->Get("h_temp2"+TString(rootfilename));
		TF1 *fit = new TF1("fit"+TString(rootfilename),"[0]*x+[1]",0,t_out->GetEntries());
		h_mon_s->Fit("fit"+TString(rootfilename));
		h_mon_s->SetMarkerStyle(20);
		h_mon_s->SetTitle(Form("Drift on the monitor corresponding to the step %s;step;number of photons",rootfilename));
		gStyle->SetOptStat("");
		h_mon_s->Draw();
		Double_t k = fit->GetParameter(0);
		Double_t A = fit->GetParameter(1);
		//Printf("slope: %f und intercept: %f",k,A);
		*/
		
		mon_d->SaveAs(TString(strFullpath)+TString("monitor_drift_step_fit_all_tiles")+TString(".png"));

		C = TMath::Mean(t_out->GetSelectedRows(),t_out->GetV1()); //const to which all the values will be adjusted
		factor = mean_of_all_monitors/C; //this is the correction to put all of the Tiles on the same level

		//Plot the scan with calibrated values
		//Canvas Labeling
		TCanvas* Scan_cor = new TCanvas("Scan_cor"+TString(rootfilename),"Scan plot corrected for all tiles: "+TString(rootfilename),3000,3000);
		Scan_cor->cd();
	
		//create Histogram for the corrected values
		TH2F* h_cor = new TH2F("h_cor"+TString(rootfilename),"3D Scan corrected for all tiles "+TString(rootfilename),15,0,300,14,0,280);
		t_out->Project("h_cor"+TString(rootfilename),"y:x",Form("LY_tot_nph*%f*%f/(%f*Entry$+%f)*(y<300)",C,factor,k,A)); //y<300 so that the monitor is not shown
		h_cor->SetTitle(Form("Light per point (corrected the mean %f to %f photons for all tiles) %s;x-position;y-position",C,mean_of_all_monitors,rootfilename));
		gStyle->SetOptStat("");
		h_cor->Draw("colz");
		Scan_cor->SaveAs(TString(strFullpath)+TString("scan_cor_all_tiles")+TString(".png"));


		//Plot the error of the scan with calibrated values
		//Canvas Labeling
		TCanvas* Scan_cor_e = new TCanvas("Scan_cor_e"+TString(rootfilename),"Scan error plot corrected for all tiles: "+TString(rootfilename),3000,3000);
		Scan_cor_e->cd();
		//create Histogram for the error of the corrected values
		TH2F* h_cor_e = new TH2F("h_cor_e"+TString(rootfilename),"3D Scan of the error corrected for all tiles "+TString(rootfilename), 15,0,300,14,0,280);
		t_out->Project("h_cor_e"+TString(rootfilename),"y:x",Form("LY_tot_nph_rms*%f*%f/(%f*Entry$+%f)*(y<300)",C,factor,k,A)); //y<300 so that the monitor is not shown
		h_cor_e->SetTitle(Form("Light error per point (corrected the mean %f to %f photons for all tiles) %s;x-position;y-position",C,mean_of_all_monitors,rootfilename));
		gStyle->SetOptStat("");
		h_cor_e->Draw("colz");
		//Scan_cor_e->SaveAs(TString(strFullpath)+TString("scan_cor_err_all_tiles")+TString(".png"));

		float_t LY_tot_nph_rms_squ[t_out->GetSelectedRows()];
		for(int i=0;i<t_out->GetSelectedRows();i++){
			LY_tot_nph_rms_squ[i]=t_out->GetW()[i]*t_out->GetW()[i];
			//printf("weight is: %f \n",LY_tot_nph_rms_squ[i]);
		}
		sum_error = sqrt(arr_sum(LY_tot_nph_rms_squ,t_out->GetSelectedRows()));
		printf("Sum error is %f \n", sum_error);

		//calculate the total light (with the sum of all bins)
		sum = h_cor->Integral(0,-1,0,-1);
		printf("The sum is: %f \n",sum);

		//each SiPM plotted
		//Canvas Labeling
		TCanvas* Scan_s_c = new TCanvas("Scan_s_c"+TString(rootfilename),"Scan plot for each SiPM corrected for all tiles: "+TString(rootfilename),3000,3000);
		Scan_s_c->DivideSquare(6,0.01,0.01,0);
		Scan_s_c->cd();

		//create Histogram
		for(int i=0;i<6;i++){
			Scan_s_c->cd(i+1);
			TH2F* h_c = new TH2F(Form("h_c%d%s",i,rootfilename),Form("3D Scan SiPMs corrected mean %f to %f: %s",C,mean_of_all_monitors,rootfilename), 15,0,300,14,0,280);
			t_out->Project(Form("h_c%d%s",i,rootfilename),"y:x",Form("LY_nph[%d]*%f*%f/(%f*Entry$+%f)*(y<300)",i,C,factor,k,A)); //y<300 so that the monitor is not shown
			h_c->SetTitle(Form("Light per point for SiPM %d corrected mean  %f to %f photons: %s;x-position;y-position",i+1,C,mean_of_all_monitors,rootfilename));
			h_c->Draw("colz");
		}
		Scan_s_c->SaveAs(TString(strFullpath)+TString("scan_SiPM_cor_all_tiles")+TString(".png"));
	}

	sum_and_error[0]=sum;
	sum_and_error[1]=sum_error;	

	return sum_and_error;
}
