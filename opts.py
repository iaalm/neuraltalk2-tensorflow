import argparse

def parse_opt():
    parser = argparse.ArgumentParser()
    # Data input settings
    parser.add_argument('--input_json', type=str, default='data/coco.json',
                    help='path to the json file containing additional info and vocab')
    parser.add_argument('--input_h5', type=str, default='data/coco.json',
                    help='path to the h5file containing the preprocessed dataset')
    #parser.add_argument('--image_path', type=str, default='data/coco',
    #                help='image directory containing images')
    #parser.add_argument('--vocab_info', type=str, default='',
    #                help='The json file saving the vocabulary information')
    parser.add_argument('--cnn_model', type=str, default='models/vgg16.npy',
                    help='path to CNN tf model. Note this MUST be a VGGNet-16 right now.')
    parser.add_argument('--start_from', type=str, default=None,
                    help="""continue training from saved model at this path. Path must contain files saved by previous training process: 
                        'infos.pkl'         : configuration;
                        'checkpoint'        : paths to model file(s) (created by tf).
                                              Note: this file contains absolute paths, be careful when moving files around;
                        'model.ckpt-*'      : file(s) with model definition (created by tf)
                    """)

    # Optimization:general

    # Model settings
    parser.add_argument('--rnn_size', type=int, default=512,
                    help='size of RNN hidden state')
    parser.add_argument('--num_layers', type=int, default=1,
                    help='number of layers in the RNN')
    parser.add_argument('--rnn_type', type=str, default='lstm',
                    help='rnn, gru, or lstm')
    parser.add_argument('--input_encoding_size', type=int, default=512,
                    help='the encoding size of each token in the vocabulary, and the image.')
    parser.add_argument('--drop_prob_lm', type=float, default=0.5,
                    help='strength of dropout in the Language Model RNN')
  
    # training setting

    # Optimization: General
    parser.add_argument('--max_epochs', type=int, default=-1,
                    help='number of epochs')
    parser.add_argument('--batch_size', type=int, default=16,
                    help='minibatch size')
    parser.add_argument('--grad_clip', type=float, default=0.1, #5.,
                    help='clip gradients at this value')
    parser.add_argument('--finetune_cnn_after', type=int, default=-1,
                    help='After what iteration do we start finetuning the CNN? (-1 = disable; never finetune, 0 = finetune from start)')
    parser.add_argument('--seq_length', type=int, default=16,
                    help='RNN sequence length')
    parser.add_argument('--seq_per_img', type=int, default=5,
                    help='number of captions to sample for each image during training. Done for efficiency since CNN forward pass is expensive. E.g. coco has 5 sents/image')
    parser.add_argument('--beam_size', type=int, default=1,
                    help='used when sample_max = 1, indicates number of beams in beam search. Usually 2 or 3 works well. More is not better. Set this to 1 for faster runtime but a bit worse performance.')

    #Optimization: for the Language Model
    parser.add_argument('--learning_rate', type=float, default=4e-4,
                    help='learning rate')
    parser.add_argument('--decay_rate', type=float, default=1,
                    help='decay rate for rmsprop')   
    #Optimization: for the CNN
    parser.add_argument('--cnn_learning_rate', type=float, default=1e-5,
                    help='learning rate for the CNN')

    # Evaluation/Checkpointing
    parser.add_argument('--id', type=str, default='',
                    help='an id identifying this run/job. used in cross-val and appended when writing progress files')
    parser.add_argument('--val_images_use', type=int, default=3200,
                    help='how many images to use when periodically evaluating the validation loss? (-1 = all)')
    parser.add_argument('--save_checkpoint_every', type=int, default=2500,
                    help='how often to save a model checkpoint?')
    parser.add_argument('--checkpoint_path', type=str, default='save',
                    help='directory to store checkpointed models')
    parser.add_argument('--language_eval', type=int, default=0,
                    help='Evaluate language as well (1 = yes, 0 = no)? BLEU/CIDEr/METEOR/ROUGE_L? requires coco-caption code from Github.')
    parser.add_argument('--losses_log_every', type=int, default=25,
                    help='How often do we snapshot losses, for inclusion in the progress dump? (0 = disable)')       
    parser.add_argument('--load_best_score', type=int, default=1,
                    help='Do we load previous best score when resuming training.')       

    args = parser.parse_args()

    return args