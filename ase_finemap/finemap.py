from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals 
from __future__ import absolute_import

import numpy as np 
import scipy.linalg.lapack as lp
import itertools

from .evaluator import Evaluator

class Finemap(object):

	NUM_CAUSAL_PRIOR_DEFAULT = 1.
	CROSS_CORR_PRIOR_DEFAULT = 0.
	IMBALANCE_HERIT_PRIOR_DEFAULT = 0.4
	TOTAL_EXP_HERIT_PRIOR_DEFAULT = 0.05
	LD_ADJ_PRIOR_DEFAULT = 1.

	def __init__(self, **kwargs):
		self.num_snps = kwargs.get("num_snps", None)
		self.num_ppl = kwargs.get("num_ppl", None)
		self.as_only = kwargs.get("as_only", False)
		self.qtl_only = kwargs.get("qtl_only", False)
			
		self.num_causal_prior = kwargs.get("num_causal_prior", NUM_CAUSAL_PRIOR_DEFAULT)	
		self.cross_corr_prior = kwargs.get("cross_corr_prior", CROSS_CORR_PRIOR_DEFAULT)
		self.imbalance_herit_prior = kwargs.get("imbalance_herit_prior", IMBALANCE_HERIT_PRIOR_DEFAULT)
		self.total_exp_herit_prior = kwargs.get("total_exp_herit_prior", TOTAL_EXP_HERIT_PRIOR_DEFAULT)
		self.ld_adj_prior = kwargs.get("ld_adj_prior", LD_ADJ_PRIOR_DEFAULT)

		self.causal_status_prior = kwargs.get("causal_status_prior", None)
		self.imbalance_var_prior = kwargs.get("imbalance_var_prior", None)
		self.total_exp_var_prior = kwargs.get("total_exp_var_prior", None)

		self.imbalance_stats = kwargs.get("imbalance_stats", None)
		self.imbalance_corr = kwargs.get("imbalance_corr", None)
		self.total_exp_stats = kwargs.get("total_exp_stats", None)
		self.total_exp_corr = kwargs.get("total_exp_corr", None)
		self.corr_stats = kwargs.get("corr_stats", None)
		self.corr_shared = kwargs.get("corr_shared", None)
		self.cross_corr = kwargs.get("cross_corr", None)

		self.imbalance = kwargs.get("imbalance", None)
		self.phases = kwargs.get("phases", None)
		self.total_exp = kwargs.get("total_exp", None)
		self.genotypes_comb = kwargs.get("genotypes_comb", None)

		self.overdispersion = kwargs.get("overdispersion", None)
		self.imbalance_errors = kwargs.get("imbalance_errors", None)
		self.exp_errors = kwargs.get("exp_errors", None)

		self.counts_A = kwargs.get("counts_A", None)
		self.counts_B = kwargs.get("counts_B", None)

		self.hap_A = kwargs.get("hap_A", None)
		self.hap_B = kwargs.get("hap_B", None)
		self.hap_vars = kwargs.get("hap_vars", None)

		self.phi = kwargs.get("phi", None)
		self.beta = kwargs.get("beta", None)

		self._mean = None
		self._beta_normalizer = None

		self._covdiag_phi = None
		self._covdiag_beta = None

		self._haps_pooled = None

		self.evaluator = None
	
	def _calc_num_snps(self):
		if self.num_snps is not None:
			return

		self.num_snps = np.size(self.counts_A)

	def _calc_num_ppl(self):
		if self.num_ppl is not None:
			return

		self.num_ppl = np.shape(self.hap_A)[0]

	def _calc_causal_status_prior(self):
		if self.causal_status_prior is not None:
			return

		self._calc_num_snps()

		self.causal_status_prior = self.num_causal_prior / self.num_snps

	# def _calc_hap_vars(self):
	# 	if self.hap_vars is not None:
	# 		return

	# 	haps_pooled = np.append(self.hap_A, self.hap_B, axis=0)
	# 	self.hap_vars = np.var(haps_pooled, axis=0)

	def _calc_imbalance(self):
		if self.imbalance is not None:
			return

		imbalance_raw = np.log(self.counts_A) - np.log(self.counts_B)
		counts = self.counts_A + self.counts_B
		imbalance_adj = (
			imbalance_raw
			/ (
				1
				+ 1 / counts
				* (1 + self.overdispersion * (counts - 1))
			)
		)

		self.imbalance = (
			imbalance_adj
			+ 1 / counts
			* np.sinh(imbalance_raw)
			* (1 + self.overdispersion * (counts - 1))
		)
	
	def _calc_phases(self):
		if self.phases is not None:
			return

		self.phases = self.hap_A - self.hap_B

	def _calc_total_exp(self):
		if self.total_exp is not None:
			return

		self.total_exp = self.counts_A + self.counts_B

	def _calc_genotypes_comb(self):
		if self.genotypes_comb is not None:
			return

		self.genotypes_comb = self.hap_A + self.hap_B

	def _calc_corr_shared(self):
		if self.corr_shared is not None:
			return

		haps_pooled = np.append(self.hap_A, self.hap_B, axis=0)
		means = np.mean(haps_pooled, axis=0)
		haps_centered = haps_pooled - means
		cov = np.cov(haps_centered.T)
		covdiag = np.diag(cov)
		denominator = np.sqrt(np.outer(covdiag, covdiag))
		corr = cov / denominator
		self.corr_shared = np.nan_to_num(corr)
		np.fill_diagonal(self.corr_shared, 1.0)

	def _calc_imbalance_errors(self):
		if self.imbalance_errors is not None:
			return

		self._calc_imbalance()
		self._calc_counts()

		imbalance_raw = np.log(self.counts_A) - np.log(self.counts_B)
		counts = self.counts_A + self.counts_B
		imbalance_adj = (
			imbalance_raw
			/ (
				1
				+ 1 / counts
				* (1 + self.overdispersion * (counts - 1))
			)
		)

		self.imbalance_errors = (
			2 / counts
			* (1 + np.cosh(imbalance_adj))
			* (1 + self.overdispersion * (counts - 1))
		)

	def _calc_phi(self):
		if self.phi is not None:
			return

		self._calc_imbalance_errors()
		self._calc_phases()
		self._calc_imbalance()

		phases = self.phases
		weights = 1 / self.imbalance_errors
		denominator = 1 / (phases.T * weights * phases.T).sum(1) 
		self.phi = denominator * np.matmul(phases.T, (weights * self.imbalance)) 

	def _calc_imbalance_stats(self):
		if self.imbalance_stats is not None:
			return

		if self.qtl_only:
			self.imbalance_stats = np.empty(0)

		self._calc_imbalance_errors()
		self._calc_phases()
		self._calc_imbalance()
		self._calc_phi()

		phases = self.phases
		weights = 1 / self.imbalance_errors
		denominator = 1 / (phases.T * weights * phases.T).sum(1) 
		phi = self.phi


		sqrt_weights = np.sqrt(weights)
		sum_weights = np.sum(weights)
		sum_weights_sq = np.sum(weights ** 2)
		sum_weights_sqrt = np.sum(sqrt_weights)
		residuals = (sqrt_weights * self.imbalance - sqrt_weights * (self.phases * phi).T).T
		remaining_errors = (
			np.sum(
				residuals * residuals - 1, 
				axis=0
			) 
			/ (sum_weights)
		)

		varphi = denominator * denominator * ((phases.T * weights**2 * phases.T).sum(1) * remaining_errors + (phases.T * weights * phases.T).sum(1))
		self.imbalance_stats = np.nan_to_num(phi / np.sqrt(varphi))

	def _calc_imbalance_corr(self):
		if self.imbalance_corr is not None:
			return

		if self.qtl_only:
			self.imbalance_corr = np.empty((0,0,))

		self._calc_corr_shared()
		self.imbalance_corr = self.corr_shared.copy()
		
	def _calc_beta(self):
		if self.beta is not None:
			return

		self._calc_genotypes_comb()
		self._calc_total_exp()
		self._calc_num_snps()

		genotypes_comb = self.genotypes_comb
		genotype_means = np.mean(genotypes_comb, axis=0)
		exp_mean = np.sum(self.total_exp) / self.num_snps
		genotypes_ctrd = genotypes_comb - genotype_means
		denominator = 1 / (genotypes_ctrd * genotypes_ctrd).sum(0)
		
		self.beta = denominator * genotypes_ctrd.T.dot(self.total_exp - exp_mean)
		self._mean = exp_mean
		self._beta_normalizer = denominator 

	def _calc_total_exp_errors(self):
		if self.exp_errors is not None:
			return

		self._calc_beta()
		self._calc_num_snps()

		residuals = (self.total_exp - self._mean - (self.genotypes_comb * self.beta).T).T
		self.exp_errors = np.sum(
			residuals * residuals, 
			axis=0
		) / (self.num_snps - 1)

	def _calc_total_exp_stats(self):
		if self.total_exp_stats is not None:
			return

		if self.as_only:
			self.total_exp_stats = np.empty(0)

		self._calc_beta()
		self._calc_total_exp_errors()
		self._calc_num_snps()

		genotypes_comb = self.genotypes_comb
		genotype_means = np.mean(genotypes_comb, axis=0)
		exp_mean = np.sum(self.total_exp) / self.num_snps
		genotypes_ctrd = genotypes_comb - genotype_means

		genotypes_combT = genotypes_ctrd.T
		denominator = self._beta_normalizer

		varbeta = denominator * denominator * (
			(genotypes_combT * genotypes_combT).sum(1) * self.exp_errors
		)
		self.total_exp_stats = self.beta / np.sqrt(varbeta)

	def _calc_total_exp_corr(self):
		if self.total_exp_corr is not None:
			return

		if self.as_only:
			self.total_exp_corr = np.empty((0,0,))

		self._calc_corr_shared()
		self.total_exp_corr = self.corr_shared.copy()

	def _calc_imbalance_var_prior(self):
		if self.imbalance_var_prior is not None:
			return

		coverage = np.mean(self.counts_A + self.counts_B)
		overdispersion = np.mean(self.overdispersion)
		imbalance = np.log(self.counts_A) - np.log(self.counts_B)
		ase_inherent_var = np.var(imbalance)

		ase_count_var = (
			2 / coverage
			* (
				1 
				+ (
					1
					/ (
						1 / (np.exp(ase_inherent_var / 2))
						+ 1 / (np.exp(ase_inherent_var / 2)**3)
						* (
							(np.exp(ase_inherent_var * 2) + 1) / 2
							- np.exp(ase_inherent_var)
						)
					)
				)
			)
			* (1 + overdispersion * (coverage - 1))
		)
		correction = ase_inherent_var / (ase_inherent_var + ase_count_var)
		self._imb_herit_adj = self.imbalance_herit_prior * correction

		self.imbalance_var_prior = (
			self.num_ppl 
			/ self.num_causal_prior 
			* self._imb_herit_adj
			/ (1 - self._imb_herit_adj)
		)

	def _calc_total_exp_var_prior(self):
		if self.total_exp_var_prior is not None:
			return

		self.total_exp_var_prior = (
			self.num_ppl 
			/ self.num_causal_prior 
			* self.total_exp_herit_prior 
			/ (1 - self.total_exp_herit_prior)
		)

	def _calc_corr_stats(self):
		if self.corr_stats is not None:
			return

		_calc_imbalance_var_prior()

		self.corr_stats = self.cross_corr_prior * np.sqrt(
			(self.num_ppl / self.num_causal_prior)**2 
			* self.total_exp_herit_prior 
			* self._imb_herit_adj
			/ (
				(
					self.num_causal_prior * self.ld_adj_prior 
					+ eqtl_herit * (self.num_ppl / self.num_causal_prior - 1)
				)
				* (
					self.num_causal_prior * self.ld_adj_prior 
					+ self._imb_herit_adj * (self.num_ppl / self.num_causal_prior - 1)
				)
			)
		)

	def _calc_cross_corr(self):
		if self.cross_corr is not None:
			return

		self._calc_imbalance_stats()
		self._calc_total_exp_stats()
		self._calc_imbalance_corr()
		self._calc_total_exp_corr()
		self._calc_imbalance_var_prior()
		self._calc_total_exp_var_prior()
		self._calc_corr_stats()
		self._calc_num_snps()

		if self.qtl_only:
			self.cross_corr = np.zeros(shape=(self.num_snps,0))
			return

		elif self.as_only:
			self.cross_corr = np.zeros(shape=(0,self.num_snps))
			return

		self.cross_corr = self.corr_shared * self.corr_stats

	def initialize(self):
		self._calc_causal_status_prior()
		self._calc_imbalance_stats()
		self._calc_total_exp_stats()
		self._calc_imbalance_corr()
		self._calc_total_exp_corr()
		self._calc_cross_corr()

		self.evaluator = Evaluator(self)

	def search_exhaustive(self, min_causal, max_causal):
		m = self.num_snps
		configuration = np.zeros(m)
		for k in xrange(min_causal, max_causal + 1):
			for c in itertools.combinations(xrange(m), k):
				np.put(configuration, c, 1)
				self.evaluator.eval(configuration)
				configuration[:] = 0

	def search_shotgun(self, min_causal, max_causal, prob_threshold, streak_threshold, num_iterations):
		m = self.num_snps
		configs = [np.zeros(m)]

		cumu_lposts = None
		streak = 0
		for i in xrange(num_iterations):
			lposts = []
			before_cumu_lposts = self.evaluator.cumu_lposts
			for c in configs:
				record_prob = np.count_nonzero(c) >= min_causal
				in_results = (tuple(c) in self.evaluator.results)
				sel_lpost = self.evaluator.eval(c, save_result=record_prob)
				lposts.append(sel_lpost)

			after_cumu_lposts = self.evaluator.cumu_lposts
			if not after_cumu_lposts:
				diff_cumu_posts = 0
			elif before_cumu_lposts:
				diff_cumu_posts = np.exp(after_cumu_lposts) - np.exp(before_cumu_lposts)
			else:
				diff_cumu_posts = np.exp(after_cumu_lposts)

			if diff_cumu_posts <= prob_threshold:
				streak += 1
			else:
				streak = 0

			if streak >= streak_threshold:
				break

			lposts = np.array(lposts)
			lpostmax = np.max(lposts)
			posts = np.exp(lposts - lpostmax)
			dist = posts / np.sum(posts)
			selection = np.random.choice(np.arange(len(configs)), p=dist)
			configuration = configs[selection]

			sel_lpost = lposts[selection]

			num_causal = np.count_nonzero(configuration)
			configs = []
			for ind in xrange(m):
				val = configuration[ind]
				# Add causal variant
				if (val == 0) and (num_causal < max_causal):
					neighbor = configuration.copy()
					neighbor[ind] = 1
					configs.append(neighbor)
				# Remove causal variant
				elif val == 1:
					neighbor = configuration.copy()
					neighbor[ind] = 0
					configs.append(neighbor)
				# Swap status with other variants
				for ind2 in xrange(ind+1, m):
					val2 = configuration[ind2]
					if val2 != val:
						neighbor = configuration.copy()
						neighbor[ind] = val2
						neighbor[ind2] = val
						configs.append(neighbor)

	def get_probs(self):
		return self.evaluator.get_probs()

	def get_probs_sorted(self):
		return self.evaluator.get_probs_sorted()

	def get_causal_set(self, confidence):
		return self.evaluator.get_causal_set(confidence)

	def get_ppas(self):
		return self.evaluator.get_ppas()

	def get_size_probs(self):
		return self.evaluator.get_size_probs()

	def reset_mapping(self):
		self.evaluator.reset()

	def coloc_clpps(self, other):
		return self.get_ppas() * other.get_ppas()

	def coloc_hyps(self, other):
		ppas1 = self.get_ppas()
		ppas2 = other.get_ppas()

		h4 = np.sum(ppas1 * ppas2)
		h3 = np.sum(ppas1) * np.sum(ppas2) - h4
		h0 = (1 - np.sum(ppas1)) * (1 - np.sum(ppas2))
		h1 = np.sum(ppas1) * (1 - np.sum(ppas2))
		h2 = (1 - np.sum(ppas1)) * np.sum(ppas2)
		
		return h0, h1, h2, h3, h4

	@classmethod
	def multi_coloc_clpps(cls, instances):
		clpps = 1.
		for i in instances:
			clpps *= i.get_ppas()
