import json
import copy


def convertFeatsToStr(feats):
    result = []
    for slot in feats:
        value = feats[slot]
        result.append(slot+'="'+value+'"')
    return ','.join(result)


def _hasType(action, act):
    for item in action:
        if act == item['act']:
            return True
    
    return False


def _hasTypeSlot(action, act, slot):
    for item in action:
        if act == item['act']:
            for slotvalue in item['slots']:
                if slot == slotvalue[0]:
                    return True
    
    return False


def _getTypeSlot(action, act, slot):
    for item in action:
        if act == item['act']:
            for slotvalue in item['slots']:
                if slot == slotvalue[0]:
                    return slotvalue[1]
    
    return ''


def _getCurrentInformedVenue(sact):
    if _hasTypeSlot(sact, 'offer', 'name'):
        return _getTypeSlot(sact, 'offer', 'name')
    return ''


def simplify_belief(ontology, belief):
    '''
    Make the give belief printable by pruning slot values with less than 0.1 belief
    '''
    simple_belief = copy.deepcopy(belief)
    for slot in simple_belief['beliefs']:
        if slot in ontology['informable']:
            simple_belief['beliefs'][slot] = \
                dict((k, p) for k, p in simple_belief['beliefs'][slot].iteritems() if p > 0.1)
    del simple_belief['features']['inform_info']
    if 'states' in simple_belief:
        del simple_belief['states']
    return simple_belief


def _addprob(sluhyps, hyp, prob):
    score = min(1.0, float(prob))
    sluhyps[json.dumps(hyp)] += score
    return sluhyps


def _normaliseandsort(sluhyps):
    result = []
    sortedhyps = sluhyps.items()
    sortedhyps.sort(key=lambda x:-x[1])
    total_score = sum(sluhyps.values())
    for hyp, score in sortedhyps:
        result.append({"score":min(1.0,score/total_score), "slu-hyp":json.loads(hyp)})
    return result

def _transformAct(act, valueTrans,ontology=None, user=True):

    if user:
        act_without_null = []
        for this_act in act:
            # another special case, to get around deny(name=none,name=blah):
            if this_act["act"] == "deny" and this_act["slots"][0][1] == "none" :
                continue
            # another special case, to get around deny(name=blah,name):
            if this_act["act"] == "inform" and this_act["slots"][0][1] == None :
                continue
            # another special case, to get around deny(name,name=blah):
            if this_act["act"] == "deny" and this_act["slots"][0][1] == None :
                continue
            act_without_null.append(this_act)
        act = act_without_null;

    # one special case, to get around confirm(type=restaurant) in Mar13 data:
    if not user and ontology!=None and "type" not in ontology["informable"] :
        for this_act in act:
            if this_act["act"] == "expl-conf" and this_act["slots"] == [["type","restaurant"]] :
                act = [{"act":"confirm-domain","slots":[]}]

    for i in range(0,len(act)):
        for j in range(0, len(act[i]["slots"])):
            act[i]["slots"][j][:] = [valueTrans[x] if x in valueTrans.keys() else x for x in act[i]["slots"][j]]

    # remove e.g. phone=dontcare and task=find
    if ontology != None:
        new_act = []
        for a in act:
            new_slots = []
            for slot,value in a["slots"]:
                keep = True
                if slot not in ["slot","this"] and (slot not in ontology["informable"]) :
                    if user or (slot not in ontology["requestable"]+["count"]) :
                        keep = False
                if keep :
                    new_slots.append((slot,value))
            if len(a["slots"]) == 0 or len(new_slots)>0 :
                a["slots"] = new_slots
                new_act.append(a)
    else :
        new_act = act

    return new_act

def print_obs(obs):
    hypstr = ''.join(obs.charArray)
    hyplist = hypstr.split('\t')
    for i in range(len(hyplist)):
        print hyplist[i], obs.doubleArray[i]

def order_using(l, lookup) :
    def _index(item):
        try :
            return lookup.index(item)
        except ValueError :
            return len(lookup)
    return sorted(l, key = _index)
