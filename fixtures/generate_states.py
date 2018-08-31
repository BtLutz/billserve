state_dict = {'AL': 'Alabama',
                  'AK': 'Alaska',
                  'AZ': 'Arizona',
                  'AR': 'Arkansas',
                  'CA': 'California',
                  'CO': 'Colorado',
                  'CT': 'Connecticut',
                  'DE': 'Delaware',
                  'DC': 'District of Columbia',
                  'FL': 'Florida',
                  'GA': 'Georgia',
                  'HI': 'Hawaii',
                  'ID': 'Idaho',
                  'IL': 'Illinois',
                  'IN': 'Indiana',
                  'IA': 'Iowa',
                  'KS': 'Kansas',
                  'KY': 'Kentucky',
                  'LA': 'Louisiana',
                  'ME': 'Maine',
                  'MD': 'Maryland',
                  'MA': 'Massachusetts',
                  'MI': 'Michigan',
                  'MN': 'Minnesota',
                  'MS': 'Mississippi',
                  'MO': 'Missouri',
                  'MT': 'Montana',
                  'NE': 'Nebraska',
                  'NV': 'Nevada',
                  'NH': 'New Hampshire',
                  'NJ': 'New Jersey',
                  'NM': 'New Mexico',
                  'NY': 'New York',
                  'NC': 'North Carolina',
                  'ND': 'North Dakota',
                  'OH': 'Ohio',
                  'OK': 'Oklahoma',
                  'OR': 'Oregon',
                  'PA': 'Pennsylvania',
                  'RI': 'Rhode Island',
                  'SC': 'South Carolina',
                  'SD': 'South Dakota',
                  'TN': 'Tennessee',
                  'TX': 'Texas',
                  'UT': 'Utah',
                  'VT': 'Vermont',
                  'VA': 'Virginia',
                  'WA': 'Washington',
                  'WV': 'West Virginia',
                  'WI': 'Wisconsin',
                  'WY': 'Wyoming',
                  'MP': 'Northern Mariana Islands',
                  'AS': 'American Samoa',
                  'GU': 'Guam',
                  'PR': 'Puerto Rico',
                  'VI': 'U.S. Virgin Islands',
                  'UM': 'U.S. Minor Outlying Islands',
                  'FM': 'Micronesia',
                  'MH': 'Marshall Island',
                  'PW': 'Palau'}


def make(pk, name, abbreviation):
    return (""""{
  \"model\": \"billserve.state\",
  \"pk\": \"%s\",
  \"fields\": {
    \"abbreviation\": \"%s\",
    \"name\": \"%s\"
  }
},
""" % (pk, abbreviation, name))


print(make(2, 'Ohio', 'OH'))
pk = 1
with open('states.json', 'w') as f:
    for state in state_dict:
        state_name = state_dict[state]
        data = make(pk, state_name, state)
        f.write(data)
        pk += 1
