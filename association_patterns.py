# -*- coding: UTF-8 -*-

import sys
import os
import itertools 
import operator

reload(sys)
sys.setdefaultencoding('utf8')

__author__ = "Katie Fotion"
__date__ = "$Feb 13, 2017 5:46:13 PM$"
    
min_support = 5
k = 5
N = 100

# Create file that contains path names to files for sentence splitter
def create_path_file(filename):
    sourceEncoding = "iso-8859-1"
    targetEncoding = "utf-8"
    with open(filename, 'w') as f:
        for file in os.listdir("./data"):
            if file.endswith(".txt"):
                dataFile = '/Users/katie/NetBeansProjects/associationPatterns/src/data/' + file
                source = open(dataFile)
                target = open(dataFile.strip('.txt')+'-2', "w")
                target.write(unicode(source.read(), sourceEncoding).encode(targetEncoding))
                f.write(dataFile.strip('.txt')+'-2\n')

# Preprocess candidate family sentences from file 
# to remove non-alphanumeric characters, white spaces, etc.
# and combine two+ word diseases into single token 
def clean_up_words(filename):
    
    diseases = ['breast cancer', 'colon cancer', 'gastric carcinoma', 'lung cancer', 
                'prostate cancer', 'renal ca', 'throat cancer', 'acute myocardinal infarction',
                'congestive heart failure', 'coronary artery disease', 'myocardial infarction', 'valvular heart disease',
                'vascular strokes', 'substance abuse', 'using substance', 'drug addict', 'heart failure', 'heart disease',
                'heart attack', 'coronary heart disease', 'nervous breakdowns', 'mood disorder/bipolar', 
                'mood disorder', 'mental illness', 'bipolar disorder',  
                'brain aneurysm', 'cerebral aneurysm', 'cerebrovascular accident', 
                'adult-onset diabetes', 'diabetes mellitus', 'type 2 diabetes', 'alcohol abuse', 
                'alcohol to excess', 'alcohol use', 'deceased from alcohol']
    
    # Read file from sentence splitter results
    with open(filename, 'r') as f:
        sentences = f.readlines()
        
    full_clean_sentences = list()
    
    # Iterate through each sentence
    for sentence in sentences:
        
        # Replace every multi word disease with underscores 
        for disease in diseases:
            if disease in sentence:
                sentence = sentence.replace(disease, disease.replace(' ', '_'))
        
        tokens = sentence.split(' ')
        clean_sentence = ''
        
        # Remove unnecessary characters from tokens 
        for token in tokens:
            if token != ' ' and token != '':
                token = token.lower().replace('\x0A', '').strip('.:(){}').replace(' ', '')
                clean_sentence = clean_sentence + token + ' ' 
        
        # Append clean sentence to list of clean sentences
        full_clean_sentences.append(clean_sentence)
        
    return full_clean_sentences

# Remove stop words 
def remove_stop_words(sentences):
    
    # Define stop list
    stop_list = ['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with']
    
    bags_of_words = list(list())
    
    # Append words not in stop list to bag of words
    for sentence in sentences:
        bag = list()
        tokens = sentence.split(' ')
        for token in tokens:
            if token not in stop_list:
                bag.append(token)
                
        # Append each bag of words to the list of bags
        bags_of_words.append(bag)
    
    return bags_of_words

if __name__ == "__main__":
    
    # Define filenames 
    file_list = './filelist.txt'
    split_sentences = './familysentences.txt'
    edited_split_sentences = './editedfamilysentences.txt'
    association_pattern_file = './associationpatterns.txt'
    
    # Filter out family sentences and preprocess (i)
    create_path_file(file_list)
    os.system("python sentence_splitter_extractfamilymembers.py " + file_list + " "+ split_sentences)
    full_clean_sentences = clean_up_words(split_sentences)
    
    # Remove stop words and write sentences to file (ii)
    bags_of_words = remove_stop_words(full_clean_sentences)
    with open(edited_split_sentences, 'w') as f:
        for bag in bags_of_words:
            for word in bag: 
                f.write(word + ' ')
            f.write('\n')
    
    # Call pyfim.py (eclat algorithm from KD Nuggets) 
    os.system("python pyfim.py -m1 -n872 -s-5 " + edited_split_sentences + " " + association_pattern_file)
    
    # Read in pattern associations from algorithm (iii) 
    with open(association_pattern_file, 'r') as f:
        patterns = f.readlines()
    
    # Filter out associations whose span is too large (iv) 
    final_pattern_associations = list()
    for pattern in patterns:
        if pattern not in final_pattern_associations:
            tokens = pattern.split(" ")
            spans = list()
            
            # Check if pattern association is of more than one word
            if len(tokens) > 2:
                support = tokens[len(tokens)-1].replace('\x0A','').strip('()')
                associated_words = tokens[0:len(tokens)-1]

                # Measure span
                for sentence in full_clean_sentences:
                    full_sentence = sentence.split(" ")

                    # Check if all associated words are found in this sentence
                    if set(associated_words) <= set(full_sentence):

                        # Measure 1st occurence of any word and last occurrence of a different word
                        for word in full_sentence:
                            if word in associated_words:
                                index_min = full_sentence.index(word)
                                first_word = word
                                break
                        for word in reversed(full_sentence):
                            if word in associated_words and word != first_word: 
                                index_max = full_sentence.index(word)
                                last_word = word
                                break

                        spans.append(index_max - index_min + 1)
            
            # Calculate the percentage of sentences that have a span of more than k words
            if len(spans) > 0:
                large_span_percentage = float(sum(i > k for i in spans))/float(len(spans))

                # Only append pattern associations that fall below 60% of sentences with too large of span
                if large_span_percentage <= 0.6:
                    final_pattern_associations.append(pattern)

    # Write final pattern associations (after iv) to file
    with open('./finalpatternassociations.txt', 'w') as f:
        for final_pattern in final_pattern_associations: 
            f.write(final_pattern)
            
    # Print number of final pattern associations
    print('After postprocessing, ' + str(len(final_pattern_associations)) + ' pattern associations were discovered')
            
    # Create wordLists with corresponding frequencies (v) 
    word_lists = dict()
    for pattern in final_pattern_associations:
        associations = pattern.split(' ')
        keywords = associations[0:len(associations)-1]
        
        # Create all ordered permutations of association patterns
        all_ordered_patterns = list(itertools.permutations(keywords))
        
        # Consider each permutation and count number of times that order occurs in a sentence
        for ordered_pattern in all_ordered_patterns:
            matched_order = 0
            for bag in bags_of_words: 
                j = 0
                for i in [0, len(bag)-1]:
                    if bag[i] == ordered_pattern[j]:
                        j = j + 1
                if j == len(ordered_pattern)-1:
                    matched_order = matched_order + 1
            
            if matched_order > 0:
                word_lists[ordered_pattern] = matched_order
    
    # Print total number of word lists
    print(str(len(word_lists)) + ' word lists discovered. The top ' + str(N) + ' will be considered:')
    
    # Find top N word lists by frequency 
    top_word_lists = sorted(word_lists.items(), key=operator.itemgetter(1))[len(word_lists)-101: len(word_lists)-1]
    
    family_words = ['mother', 'father', 'brother', 'brothers', 'sister', 'sisters', 'aunt', 'aunts', 
                    'grandfather', 'grandfathers', 'grandmother', 'grandmothers', 'uncle', 'uncles', 'son', 'sons',
                    'daughter', 'daughters', 'cousin', 'cousins', 'mom', 'dad', 'nephew', 'nephews', 'niece', 'nieces']
    
    diseases = ['breast_cancer', 'ca', 'cancer', 'colon_cancer', 'gastric_carcinoma', 'lung_cancer', 
                'prostate_cancer', 'renal_ca', 'throat_cancer', 'chf', 'cad', 'acute_myocardinal_infarction',
                'congestive_heart_failure', 'coronary_artery_disease', 'myocardial_infarction', 'valvular_heart_disease',
                'vascular_strokes', 'substance_abuse', 'using_substance', 'drug_addict', 'mi', 'heart_failure', 'heart_disease',
                'heart_attack', 'coronary_heart_disease', 'suicide', 'schizophrenia', 'nervous_breakdowns', 'mood_disorder/bipolar', 
                'mood_disorder', 'mental_illness', 'depression', 'depressed', 'bipolar_disorder', 'bipolar', 'adhd', 'htn', 
                'hypertension', 'brain_aneurysm', 'cerebral_aneurysm', 'cerebrovascular_accident', 'stroke', 'strokes',
                'adult-onset_diabetes', 'diabetes', 'diabetes_mellitus', 'dm', 'type_2_diabetes', 'alcohol_abuse', 'alcoholic', 
                'alcoholism', 'alcohol_to_excess', 'alcohol_use', 'deceased_from_alcohol']
    
    family_word_count = 0
    disease_word_count = 0
    family_no_disease = 0
    disease_no_family = 0
    both_word_count = 0
    for word_list_dict in top_word_lists: 
        word_list = word_list_dict[0]
        
        # Calculate number of word lists with at least one family member (vi.a)
        if any(word in family_words for word in word_list):
            family_word_count = family_word_count + 1
            
            # Calculate number of word lists with family and no disease (vi.c)
            if all(word not in diseases for word in word_list):
                family_no_disease = family_no_disease + 1
                
            # Calculate number of word lists with both family and disease (vi.e)
            else: 
                both_word_count = both_word_count + 1
                
        # Calculate number of word lists with at least one disease (v.b)     
        if any(word in diseases for word in word_list):
            disease_word_count = disease_word_count + 1
            
            # Calculate number of word lists with disease and no family (vi.d)
            if all(word not in family_words for word in word_list):
                disease_no_family = disease_no_family + 1
            
    # Print number of frequent word lists with at least one family member
    print(str(family_word_count) + ' frequent word lists contain at least one family member')
    
    # Print number of frequent word lists with at least one disease
    print(str(disease_word_count) + ' frequent word lists contain at least one disease')
    
    # Print number of frequent word lists with family member and no diseases
    print(str(family_no_disease) + ' frequent word lists contain at least one family member and no diseases')
    
    # Print number of frequent word lists with disease and no family members
    print(str(disease_no_family) + ' frequent word lists contain at least one disease and no family members')
    
    # Print number of frequent word lists with at least one of both family members and disease s
    print(str(both_word_count) + ' frequent word lists contain at least one family member and disease')
    
    # By the set law of inclusion/exclusion, we can calculate the number of frequent word lists with neither (vi.f)
    neither_word_count = N - (both_word_count + disease_no_family + family_no_disease)
    print(str(neither_word_count) + ' frequent word lists contain neither family members nor diseases')