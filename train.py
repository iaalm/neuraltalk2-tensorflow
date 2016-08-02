from __future__ import print_function
import numpy as np
import tensorflow as tf

import time
import os
from six.moves import cPickle

import opts
import models
from dataloader import *
import eval_utils

#from ipdb import set_trace

def main():
    opt = opts.parse_opt()
    train(opt)

def train(opt):
    loader = DataLoader(opt)
    opt.vocab_size = loader.vocab_size
    model = models.setup(opt)

    
    infos = {}
    if opt.start_from is not None:
        # open old infos and check if models are compatible
        with open(os.path.join(opt.start_from, 'infos.pkl')) as f:
            infos = cPickle.load(f)
            saved_model_opt = infos['opt']
            need_be_same=["rnn_type","rnn_size","num_layers","seq_length"]
            for checkme in need_be_same:
                assert vars(saved_model_opt)[checkme]==vars(opt)[checkme],"Command line argument and saved model disagree on '%s' "%checkme

    iteration = infos.get('iter', 0)
    epoch = infos.get('epoch', 0)
    loader.iterators = infos.get('iterators', loader.iterators)
    if opt.load_best_score == 1:
        best_val_score = infos.get('best_val_score', None)
        

    model.build_model()
    model.build_generator()

    saver = tf.train.Saver(max_to_keep=10)

    with tf.Session() as sess:
        loader.assign_session(sess)

        # Initialize the variables, and restore the variables form checkpoint if there is.
        # And initialize the writer
        model.initialize(sess)
        
        sess.run(tf.assign(model.lr, opt.learning_rate * (opt.decay_rate ** epoch)))
        sess.run(tf.assign(model.cnn_lr, opt.cnn_learning_rate))

        while True:
            start = time.time()
            data = loader.get_batch(0)
            print('Read data:', time.time() - start)


            start = time.time()
            feed = {model.images: data['images'], model.labels: data['labels'], model.masks: data['masks'], model.keep_prob: 1 - model.dropout}
            if iteration >= opt.finetune_cnn_after or opt.finetune_cnn_after == -1:
                train_loss, merged, _ = sess.run([model.cost, model.summaries, model.train_op], feed)
            else:
                train_loss, merged, _, __ = sess.run([model.cost, model.self.summaries, model.train_op, model.cnn_train_op], feed)
            end = time.time()
            print("iter {} (epoch {}), train_loss = {:.3f}, time/batch = {:.3f}" \
                .format(iteration, epoch, train_loss, end - start))

            # Update the iteration and epoch
            iteration += 1
            if data['bounds']['wrapped']:
                epoch += 1

            # Write the training loss summary
            if (iteration % opt.losses_log_every == 0):
                model.writer.add_summary(merged, iteration)
                model.writer.flush()

            # make evaluation on validation set, and save model
            if (iteration % opt.save_checkpoint_every == 0):
                # eval model
                eval_kwargs = {'val_images_use': opt.val_images_use, 'split': 1, 'language_eval': opt.language_eval, 'dataset': opt.input_json}
                val_loss, predictions, lang_stats = eval_split(sess, model, loader, eval_kwargs)
                # Write into summary
                summary = tf.Summary(value=[tf.Summary.Value(tag='validation loss', simple_value=val_loss)])
                model.writer.add_summary(summary, iteration)
                for k,v in lang_stats.iteritems():
                    summary = tf.Summary(value=[tf.Summary.Value(tag=k, simple_value=v)])
                    model.writer.add_summary(summary, iteration)
                model.writer.flush()

                # Save model if is improving on validation result
                if opt.language_eval == 1:
                    current_score = lang_stats['CIDEr']
                else:
                    current_score = - val_loss

                if best_val_score is None or current_score > best_val_score: # if true
                    best_val_score = current_score
                    checkpoint_path = os.path.join(opt.checkpoint_path, 'model.ckpt')
                    #saver.save(sess, checkpoint_path, global_step = iteration)
                    saver.save(sess, checkpoint_path, global_step = iteration)
                    print("model saved to {}".format(checkpoint_path))

                    # Dump miscalleous informations
                    infos['iter'] = iteration
                    infos['epoch'] = epoch
                    infos['iterators'] = loader.iterators
                    infos['best_val_score'] = best_val_score
                    infos['opt'] = opt
                    with open(os.path.join(opt.checkpoint_path, 'infos.pkl'), 'wb') as f:
                            cPickle.dump(infos, f)

            if epoch >= opt.max_epochs and opt.max_epochs != -1:
                break

def eval_split(sess, model, loader, eval_kwargs):
    verbose = eval_kwargs.get('verbose', True)
    val_images_use = eval_kwargs.get('val_images_use', -1)
    split = eval_kwargs.get('split', 1)
    language_eval = eval_kwargs.get('language_eval', 1)
    dataset = eval_kwargs.get('dataset', 'coco')

    loader.reset_iterator(split)

    n = 0
    loss_sum = 0
    loss_evals = 0
    predictions = []
    while True:
        data = loader.get_batch(split)
        n = n + loader.batch_size

        # forward the model to get loss
        feed = {model.images: data['images'], model.labels: data['labels'], model.masks: data['masks'], model.keep_prob: 1.0}
        loss = sess.run(model.cost, feed)

        loss_sum = loss_sum + loss
        loss_evals = loss_evals + 1

        # forward the model to also get generated samples for each image
        feed = {model.images: data['images'], model.keep_prob: 1.0}
        g_o,g_l,g_p, seq = sess.run([model.g_output, model.g_logits, model.g_probs, model.generator], feed)

        #set_trace()
        sents = loader.decode_sequence(seq)

        for k, sent in enumerate(sents):
            entry = {'image_id': data['infos'][k]['id'], 'caption': sent}
            predictions.append(entry)
            if verbose:
                print('image %s: %s' %(entry['image_id'], entry['caption']))
        
        ix0 = data['bounds']['it_pos_now']
        ix1 = min(data['bounds']['it_max'], val_images_use)
        if verbose:
            print('evaluating validation preformance... %d/%d (%f)' %(ix0 - 1, ix1, loss))

        if data['bounds']['wrapped']:
            break
        if n>= val_images_use:
            break

    if language_eval == 1:
        lang_stats = eval_utils.language_eval(dataset, predictions)
    return loss_sum/loss_evals, predictions, lang_stats


if __name__ == '__main__':
    main()