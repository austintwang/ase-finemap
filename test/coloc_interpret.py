import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['agg.path.chunksize'] = 10000
import seaborn as sns
import matplotlib.pyplot as plt

try:
	import pickle as pickle
except ImportError:
	import pickle

def load_data(data_dir, test_name):
	# print(os.listdir(data_dir)) ####
	filenames = [os.path.join(data_dir, i) for i in os.listdir(data_dir) if i.endswith(".pickle")]
	data_list = []
	for i in filenames:
		# print(i) ####
		with open(i, "rb") as data_file:
			data = pickle.load(data_file)
		data_list.extend(data)

	data_df = pd.DataFrame.from_records(data_list)
	# print(data_df.columns.values) ####
	return data_df

def make_heatmap(
		df, 
		var_row, 
		var_col, 
		response, 
		model_name, 
		title, 
		result_path, 
		aggfunc="mean",
		fmt='.2g'
	):
	heat_data = pd.pivot_table(
		df, 
		values=response, 
		index=var_row, 
		columns=var_col, 
		aggfunc=aggfunc
	)

	sns.heatmap(heat_data, annot=True, fmt=fmt, square=True)
	plt.title(title)
	plt.savefig(result_path)
	plt.clf()

def interpret_shared(
		data_dir_base, 
		gwas_herits, 
		model_flavors,
		res_dir_base
	):
	data_dir = os.path.join(data_dir_base, "shared")
	df = load_data(data_dir, "shared")

	res_dir = os.path.join(res_dir_base, "shared")
	if not os.path.exists(res_dir):
		os.makedirs(res_dir)

	var_row = "GWAS Sample Size"
	var_col = "QTL Sample Size"
	response = "Colocalization Score (PP4)"

	sns.set(font="Roboto")

	for h in gwas_herits:
		if "full" in model_flavors:
			df_model = df.loc[
				(df["model"] == "full")
				& (df["herit_gwas"] == h)
				& (df["complete"] == True)
			]
			df_model.rename(
				columns={
					"num_samples_gwas": var_row,
					"num_samples_qtl": var_col,
					"h4": response,
				}, 
				inplace=True
			)
			model_name = "PLASMA/C-JC"
			title = "Mean {0}\n{1} Model, GWAS Heritability = {2:.0E}".format(response, model_name, h)
			result_path = os.path.join(res_dir, "full_h_{0}.svg".format(h))
			make_heatmap(
				df_model, 
				var_row, 
				var_col, 
				response, 
				model_name, 
				title, 
				result_path, 
				aggfunc="mean",
				fmt='.2g'
			)
		if "indep" in model_flavors:
			df_model = df.loc[
				(df["model"] == "indep")
				& (df["herit_gwas"] == h)
				& (df["complete"] == True)
			]
			# print(df_model.columns.values) ####
			df_model.rename(
				columns={
					"num_samples_gwas": var_row,
					"num_samples_qtl": var_col,
					"h4": response,
				}, 
				inplace=True
			)
			# print(df_model.columns.values) ####
			model_name = "PLASMA/C-J"
			title = "Mean {0}\n{1} Model, GWAS Heritability = {2:.0E}".format(response, model_name, h)
			result_path = os.path.join(res_dir, "indep_h_{0}.svg".format(h))
			make_heatmap(
				df_model, 
				var_row, 
				var_col, 
				response, 
				model_name, 
				title, 
				result_path, 
				aggfunc="mean",
				fmt='.2g'
			)
		if "ase" in model_flavors:
			df_model = df.loc[
				(df["model"] == "ase")
				& (df["herit_gwas"] == h)
				& (df["complete"] == True)
			]
			df_model.rename(
				columns={
					"num_samples_gwas": var_row,
					"num_samples_qtl": var_col,
					"h4": response,
				}, 
				inplace=True
			)
			model_name = "PLASMA/C-AS"
			title = "Mean {0}\n{1} Model, GWAS Heritability = {2:.0E}".format(response, model_name, h)
			result_path = os.path.join(res_dir, "ase_h_{0}.svg".format(h))
			make_heatmap(
				df_model, 
				var_row, 
				var_col, 
				response, 
				model_name, 
				title, 
				result_path, 
				aggfunc="mean",
				fmt='.2g'
			)
		if "ecav" in model_flavors:
			df_model = df.loc[
				(df["model"] == "ecav")
				& (df["herit_gwas"] == h)
				& (df["complete"] == True)
			]
			df_model.rename(
				columns={
					"num_samples_gwas": var_row,
					"num_samples_qtl": var_col,
					"h4": response,
				}, 
				inplace=True
			)
			model_name = "eCAVIAR"
			title = "Mean {0}\n{1} Model, GWAS Heritability = {2:.0E}".format(response, model_name, h)
			result_path = os.path.join(res_dir, "ecav_h_{0}.svg".format(h))
			make_heatmap(
				df_model, 
				var_row, 
				var_col, 
				response, 
				model_name, 
				title, 
				result_path, 
				aggfunc="mean",
				fmt='.2g'
			)
		if "eqtl" in model_flavors:
			df_model = df.loc[
				(df["model"] == "eqtl")
				& (df["herit_gwas"] == h)
				& (df["complete"] == True)
			]
			df_model.rename(
				columns={
					"num_samples_gwas": var_row,
					"num_samples_qtl": var_col,
					"h4": response,
				}, 
				inplace=True
			)
			model_name = "QTL-Only"
			title = "Mean {0}\n{1} Model, GWAS Heritability = {2:.0E}".format(response, model_name, h)
			result_path = os.path.join(res_dir, "eqtl_h_{0}.svg".format(h))
			make_heatmap(
				df_model, 
				var_row, 
				var_col, 
				response, 
				model_name, 
				title, 
				result_path, 
				aggfunc="mean",
				fmt='.2g'
			)

	df_model = df.loc[df["model"] == model_name]

if __name__ == '__main__':
	data_dir_base = "/agusevlab/awang/job_data/sim_coloc/outs/"
	res_dir_base = "/agusevlab/awang/ase_finemap_results/sim_coloc/"
	model_flavors = set(["indep", "eqtl", "ase", "ecav"])

	gwas_herits = [.1/100, .5/1e4]
	interpret_shared(data_dir_base, gwas_herits, model_flavors, res_dir_base)